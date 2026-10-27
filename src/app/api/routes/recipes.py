# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from asyncpg import Connection  # pyright: ignore[reportMissingTypeStubs]
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from app.api.dependencies.auth import get_profile, get_profile_optional
from app.api.responses.common import MessageError, MessageResponse
from app.api.responses.definitions import COMMON_RESPONSES
from app.api.schemas.auth import AccessTokenPayload
from app.api.schemas.pagination import CursorPage
from app.api.schemas.recipe import (
    RecipeCreateDTO,
    RecipeDTO,
    RecipeQueryDTO,
    RecipeUpdate,
)
from app.constants.recipe import RECIPES_DIR
from app.core.logger import logger
from app.core.queue.recipe import recipe_queue
from app.core.registry.category import CategoryRegistry, get_category_registry
from app.jobs.recipe import ProcessRecipeImage
from app.repositories.connection import get_db
from app.services.recipe import service as RecipeService

router = APIRouter(prefix="/recipes", tags=["recipes"], responses=COMMON_RESPONSES)


@router.get(
    "/search",
    response_model=CursorPage[RecipeDTO],
    responses={
        404: {"model": MessageError, "description": "Recipe not found"},
        400: {"model": MessageError, "description": "Request invalid"},
    },
)
async def findDTO(
    filter_query: Annotated[RecipeQueryDTO, Query()],
    conn: Connection = Depends(get_db),
    access: AccessTokenPayload | None = Depends(get_profile_optional),
):
    if filter_query.mine and access is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Session invalid")

    user_id = int(access.sub) if filter_query.mine and access else None

    result = await RecipeService.getDTOWithParams(
        conn,
        name=filter_query.name,
        category=filter_query.category,
        cursor=filter_query.cursor,
        limit=filter_query.limit,
        direction=filter_query.direction,
        user_id=user_id,
    )

    return result


@router.get(
    "/recipe/{id}",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=RecipeDTO,
)
async def findId(id: int, conn: Connection = Depends(get_db)):
    result = await RecipeService.getDTO(conn, id)

    return result


@router.get("/recipe/{id}/img", response_class=FileResponse)
async def getImage(id: int, conn: Connection = Depends(get_db)):
    path = await RecipeService.getImage(conn, id)

    return FileResponse(path)


@router.post(
    "/recipe",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=MessageResponse[int],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: RecipeCreateDTO,
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
    registry: CategoryRegistry = Depends(get_category_registry),
):
    category_id = registry.get(data.category)
    new = data.to_create()
    id = await RecipeService.create(conn, new, category_id, int(access_token.sub))

    return JSONResponse({"message": id}, status_code=status.HTTP_201_CREATED)


@router.patch(
    "/recipe/{id}",
    responses={
        404: {"model": MessageError, "description": "Recipe not found"},
        400: {"model": MessageError, "description": "Request invalid"},
    },
    response_model=MessageResponse,
)
async def update(
    id: int,
    data: RecipeUpdate,
    conn: Connection = Depends(get_db),
    access_token: AccessTokenPayload = Depends(get_profile),
    registry: CategoryRegistry = Depends(get_category_registry),
):
    if not data.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Body is empty")

    new = data.to_update(registry.get(data.category) if data.category else None)
    await RecipeService.update(conn, id, int(access_token.sub), new)

    return JSONResponse({"message": "Recipe update"})


@router.put(
    "/recipe/{id}/img",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def updateAvatar(
    id: int,
    image: Annotated[UploadFile, File()],
    access_token: AccessTokenPayload = Depends(get_profile),
):
    user_id = int(access_token.sub)
    recipe_dir = Path("/tmp/recipe") / str(user_id)
    recipe_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4()}.upload"  # pyright: ignore[reportUndefinedVariable]
    source_path = recipe_dir / filename

    with source_path.open("wb") as file:
        while chunk := await image.read(1024 * 1024):
            file.write(chunk)

    job = ProcessRecipeImage.new(user_id=user_id, recipe_id=id, source_path=source_path)
    await recipe_queue.enqueue(job)

    return JSONResponse(
        {"message": "Avatar processing"}, status_code=status.HTTP_202_ACCEPTED
    )


@router.delete("/recipe/{id}/img", response_model=MessageResponse)
async def deleteAvatar(
    id: int,
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    user_id = int(access_token.sub)

    old_avatar_key = await RecipeService.updateImage(conn, id, user_id, None)

    if old_avatar_key:
        path = RECIPES_DIR / f"{old_avatar_key}.webp"

        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Failed to delete avatar file: %s",
                path,
            )

    return MessageResponse(message="Avatar delete")


@router.delete(
    "/recipe/{id}",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=MessageResponse,
)
async def delete(
    id: int,
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    await RecipeService.delete(conn, id, int(access_token.sub))
    return JSONResponse({"message": "Recipe delete"})
