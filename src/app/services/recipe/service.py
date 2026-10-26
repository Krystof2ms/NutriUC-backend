from pathlib import Path

from asyncpg import Connection  # pyright: ignore[reportMissingTypeStubs]

from app.api.schemas.pagination import CursorPage
from app.constants.recipe import RECIPES_DIR
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import CursorDirection, RecipeCreate, RecipeDTO, RecipeUpdate
from app.repositories.recipe import RecipeRepo

from .errors import RecipeImageNotFound, RecipeNotCreateError, RecipeNotFoundError

PAGE_SIZE = 12


@trace(TraceLayer.SERVICE)
async def updateImage(
    conn: Connection, id: int, user_id: int, image_key: str | None
) -> str | None:
    image_key_new = await RecipeRepo.updateImage(conn, id, user_id, image_key)

    return image_key_new


@trace(TraceLayer.SERVICE)
async def getImage(conn: Connection, id: int) -> Path:
    recipe = await RecipeRepo.getRecipeDB(conn, id)

    if recipe is None:
        raise RecipeImageNotFound()

    if recipe.image_key is None:
        raise RecipeImageNotFound()

    path = RECIPES_DIR / f"{recipe.image_key}.webp"

    if not path.is_file():
        raise RecipeImageNotFound()

    return path


@trace(TraceLayer.SERVICE)
async def getDTOWithParams(
    conn: Connection,
    *,
    name: str | None = None,
    category: str | None = None,
    user_id: int | None = None,
    cursor: int | None = None,
    limit: int = PAGE_SIZE,
    direction: CursorDirection = CursorDirection.NEXT,
) -> CursorPage[RecipeDTO]:
    result = await RecipeRepo.getDtoWithParams(
        conn,
        name=name,
        category=category,
        user_id=user_id,
        cursor=cursor,
        limit=limit,
        direction=direction,
    )

    if result is None:
        raise RecipeNotFoundError()

    return result


@trace(TraceLayer.SERVICE)
async def getDTO(conn: Connection, id: int) -> RecipeDTO:
    recipe = await RecipeRepo.getDTO(conn, id)

    if recipe is None:
        raise RecipeNotFoundError()

    return recipe


@trace(TraceLayer.REPO)
async def create(
    conn: Connection,
    data: RecipeCreate,
    category_id: int,
    user_id: int,
) -> int:
    id = await RecipeRepo.create(conn, data, category_id, user_id)

    if id is None:
        raise RecipeNotCreateError()

    return id


@trace(TraceLayer.SERVICE)
async def update(
    conn: Connection,
    recipe: int,
    user_id: int,
    data: RecipeUpdate,
):
    result = await RecipeRepo.update(conn, recipe, user_id, data)

    if not result:
        raise RecipeNotFoundError()


@trace(TraceLayer.SERVICE)
async def delete(
    conn: Connection,
    recipe: int,
    user_id: int,
):
    result = await RecipeRepo.deleteById(conn, recipe, user_id)

    if not result:
        raise RecipeNotFoundError()
