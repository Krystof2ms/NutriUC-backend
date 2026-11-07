# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from app.api.dependencies.auth import get_profile
from app.api.dependencies.services import get_user_service
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
from app.services.user.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/stats", response_model=UserStats, responses=COMMON_RESPONSES)
async def summary(
    access_token: AccessTokenPayload = Depends(get_profile),
    user_service: UserService = Depends(get_user_service),
):
    response = await user_service.get_stats(int(access_token.sub))
    return response


@router.get("/me", response_model=UserSummaryMe, responses=COMMON_RESPONSES)
async def me(
    access_token: AccessTokenPayload = Depends(get_profile),
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.getUserDB(int(access_token.sub), "user")
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
    user_service: UserService = Depends(get_user_service),
):
    if not update.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Body is empty")
    data = update.to_update()
    user_id = int(access_token.sub)
    await user_service.updateUser(user_id, data)
    return MessageResponse(message="User update")


@router.put(
    "/me/avatar", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED
)
async def update_avatar(
    avatar: Annotated[UploadFile, File()],
    crop: Annotated[Crop, Query()],
    access_token: AccessTokenPayload = Depends(get_profile),
):
    user_id = int(access_token.sub)
    avatar_dir = Path("/tmp/avatar") / str(user_id)
    avatar_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}.upload"
    source_path = avatar_dir / filename
    with source_path.open("wb") as file:
        while chunk := (await avatar.read(1024 * 1024)):
            file.write(chunk)
    job = ProcessUserAvatar.new(
        user_id=user_id, source_path=source_path, crop=crop.to_crop()
    )
    await avatar_queue.enqueue(job)
    return JSONResponse(
        {"message": "Avatar processing"}, status_code=status.HTTP_202_ACCEPTED
    )


@router.delete("/me/avatar", response_model=MessageResponse)
async def delete_avatar(
    access_token: AccessTokenPayload = Depends(get_profile),
    user_service: UserService = Depends(get_user_service),
):
    user_id = int(access_token.sub)
    old_avatar_key = await user_service.updateAvatar(user_id, None)
    if old_avatar_key:
        path = AVATAR_DIR / f"{old_avatar_key}.webp"
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Failed to delete avatar file: %s", path)
    return MessageResponse(message="Avatar delete")


@router.get("/{id}/avatar", response_class=FileResponse)
async def avatar(id: UUID, user_service: UserService = Depends(get_user_service)):
    path = await user_service.getAvatar(str(id))
    return FileResponse(path)


@router.post("/", response_model=MessageResponse)
async def create(
    data: UserCreateDTO,
    registry: RoleRegistry = Depends(get_role_registry),
    user_service: UserService = Depends(get_user_service),
):
    new = data.to_create(registry.get("user"))
    await user_service.registerUser(new)
    return MessageResponse(message="User create")
