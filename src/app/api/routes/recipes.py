# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse

from app.api.dependencies.auth import get_profile, get_profile_optional
from app.api.dependencies.services import get_recipe_service
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
from app.services.recipe.service import RecipeService

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
    access: AccessTokenPayload | None = Depends(get_profile_optional),
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    if filter_query.mine and access is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Session invalid")
    user_id = int(access.sub) if filter_query.mine and access else None
    result = await recipe_service.getDTOWithParams(
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
async def findId(id: int, recipe_service: RecipeService = Depends(get_recipe_service)):
    result = await recipe_service.getDTO(id)
    return result


@router.get("/recipe/{id}/img", response_class=FileResponse)
async def getImage(
    id: int, recipe_service: RecipeService = Depends(get_recipe_service)
):
    path = await recipe_service.getImage(id)
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
    registry: CategoryRegistry = Depends(get_category_registry),
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    category_id = registry.get(data.category)
    new = data.to_create()
    id = await recipe_service.create(new, category_id, int(access_token.sub))
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
    access_token: AccessTokenPayload = Depends(get_profile),
    registry: CategoryRegistry = Depends(get_category_registry),
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    if not data.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Body is empty")
    new = data.to_update(registry.get(data.category) if data.category else None)
    await recipe_service.update(id, int(access_token.sub), new)
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
    filename = f"{uuid4()}.upload"
    source_path = recipe_dir / filename
    with source_path.open("wb") as file:
        while chunk := (await image.read(1024 * 1024)):
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
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    user_id = int(access_token.sub)
    old_avatar_key = await recipe_service.updateImage(id, user_id, None)
    if old_avatar_key:
        path = RECIPES_DIR / f"{old_avatar_key}.webp"
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Failed to delete avatar file: %s", path)
    return MessageResponse(message="Avatar delete")


@router.delete(
    "/recipe/{id}",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=MessageResponse,
)
async def delete(
    id: int,
    access_token: AccessTokenPayload = Depends(get_profile),
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    await recipe_service.delete(id, int(access_token.sub))
    return JSONResponse({"message": "Recipe delete"})
