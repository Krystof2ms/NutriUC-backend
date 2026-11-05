from pathlib import Path

from app.api.schemas.pagination import CursorPage
from app.constants.recipe import RECIPES_DIR
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import CursorDirection, RecipeCreate, RecipeDTO, RecipeUpdate
from app.repositories.interfaces.recipe import RecipeRepositoryInterface

from .errors import RecipeImageNotFound, RecipeNotCreateError, RecipeNotFoundError

PAGE_SIZE = 12


class RecipeService:
    def __init__(self, recipe_repo: RecipeRepositoryInterface):
        self.recipe_repo = recipe_repo

    @trace(TraceLayer.SERVICE)
    async def updateImage(
        self, id: int, user_id: int, image_key: str | None
    ) -> str | None:
        image_key_new = await self.recipe_repo.updateImage(id, user_id, image_key)
        return image_key_new

    @trace(TraceLayer.SERVICE)
    async def getImage(self, id: int) -> Path:
        recipe = await self.recipe_repo.getRecipeDB(id)
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
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        user_id: int | None = None,
        cursor: int | None = None,
        limit: int = PAGE_SIZE,
        direction: CursorDirection = CursorDirection.NEXT,
    ) -> CursorPage[RecipeDTO]:
        result = await self.recipe_repo.getDtoWithParams(
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
    async def getDTO(self, id: int) -> RecipeDTO:
        recipe = await self.recipe_repo.getDTO(id)
        if recipe is None:
            raise RecipeNotFoundError()
        return recipe

    @trace(TraceLayer.REPO)
    async def create(self, data: RecipeCreate, category_id: int, user_id: int) -> int:
        id = await self.recipe_repo.create(data, category_id, user_id)
        if id is None:
            raise RecipeNotCreateError()
        return id

    @trace(TraceLayer.SERVICE)
    async def update(self, recipe: int, user_id: int, data: RecipeUpdate):
        result = await self.recipe_repo.update(recipe, user_id, data)
        if not result:
            raise RecipeNotFoundError()

    @trace(TraceLayer.SERVICE)
    async def delete(self, recipe: int, user_id: int):
        result = await self.recipe_repo.deleteById(recipe, user_id)
        if not result:
            raise RecipeNotFoundError()
