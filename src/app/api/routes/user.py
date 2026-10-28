# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from asyncpg.connection import Connection  # pyright: ignore[reportMissingTypeStubs]
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from app.api.dependencies.auth import get_profile
from app.api.responses.common import MessageError, MessageResponse
from app.api.responses.definitions import COMMON_RESPONSES
from app.api.schemas.auth import AccessTokenPayload
from app.api.schemas.user import (
    Crop,
    UserCreateDTO,
    UserStats,
    UserSummaryMe,
    UserUpdate,
)
from app.constants.avatar import AVATAR_DIR
from app.core.logger import logger
from app.core.queue import avatar_queue
from app.core.registry.roles import RoleRegistry, get_role_registry
from app.jobs.user import ProcessUserAvatar
from app.repositories.connection import get_db
from app.services.user import service as UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/stats", response_model=UserStats, responses=COMMON_RESPONSES)
async def summary(
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    response = await UserService.get_stats(conn, int(access_token.sub))

    return response


@router.get("/me", response_model=UserSummaryMe, responses=COMMON_RESPONSES)
async def me(
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    user = await UserService.getUserDB(
        conn, int(access_token.sub), "user"
    )

    data = user.to_summary_me()

    return data


@router.patch(
    "/me",
    response_model=MessageResponse,
    responses={
        **COMMON_RESPONSES,
        400: {"model": MessageError, "description": "Request invalid"},
    },
)
async def update(
    update: UserUpdate,
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    if not update.model_fields_set:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Body is empty",
        )

    data = update.to_update()
    user_id = int(access_token.sub)

    await UserService.updateUser(conn, user_id, data)

    return MessageResponse(message="User update")


@router.put(
    "/me/avatar", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED
)
async def updateAvatar(
    avatar: Annotated[UploadFile, File()],
    crop: Annotated[Crop, Query()],
    access_token: AccessTokenPayload = Depends(get_profile),
):
    user_id = int(access_token.sub)
    avatar_dir = Path("/tmp/avatar") / str(user_id)
    avatar_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}.upload"  # pyright: ignore[reportUndefinedVariable]
    source_path = avatar_dir / filename

    with source_path.open("wb") as file:
        while chunk := await avatar.read(1024 * 1024):
            file.write(chunk)

    job = ProcessUserAvatar.new(
        user_id=user_id, source_path=source_path, crop=crop.to_crop()
    )
    await avatar_queue.enqueue(job)

    return JSONResponse(
        {"message": "Avatar processing"}, status_code=status.HTTP_202_ACCEPTED
    )


@router.delete("/me/avatar", response_model=MessageResponse)
async def deleteAvatar(
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    user_id = int(access_token.sub)

    old_avatar_key = await UserService.updateAvatar(conn, user_id, None)

    if old_avatar_key:
        path = AVATAR_DIR / f"{old_avatar_key}.webp"

        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Failed to delete avatar file: %s",
                path,
            )

    return MessageResponse(message="Avatar delete")


@router.get("/{id}/avatar", response_class=FileResponse)
async def avatar(id: UUID, conn: Connection = Depends(get_db)):
    path = await UserService.getAvatar(conn, str(id))

    return FileResponse(path)


@router.post("/", response_model=MessageResponse)
async def create(
    data: UserCreateDTO,
    conn: Connection = Depends(get_db),
    registry: RoleRegistry = Depends(get_role_registry),
):
    new = data.to_create(registry.get("user"))

    await UserService.registerUser(conn, new)

    return MessageResponse(message="User create")
