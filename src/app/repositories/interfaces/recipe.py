from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.api.schemas.pagination import CursorPage
from app.models import CursorDirection, RecipeCreate, RecipeDB, RecipeDTO, RecipeUpdate
from app.repositories.const import PAGE_SIZE


class RecipeRepositoryInterface(ABC):
    @abstractmethod
    def getRecipeDB(self, id: int) -> Awaitable[RecipeDB | None]: ...

    @abstractmethod
    def getDtoWithParams(
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        user_id: int | None = None,
        cursor: int | None = None,
        limit: int = PAGE_SIZE,
        direction: CursorDirection = CursorDirection.NEXT,
    ) -> Awaitable[CursorPage[RecipeDTO] | None]: ...

    @abstractmethod
    def getDTO(self, id: int) -> Awaitable[RecipeDTO | None]: ...

    @abstractmethod
    def create(
        self, new: RecipeCreate, category_id: int, user_id: int
    ) -> Awaitable[int | None]: ...

    @abstractmethod
    def update(
        self, recipe_id: int, user_id: int, data: RecipeUpdate
    ) -> Awaitable[bool]: ...

    @abstractmethod
    def updateImage(
        self, id: int, user_id: int, image_key: str | None
    ) -> Awaitable[str | None]: ...

    @abstractmethod
    def deleteById(self, recipe_id: int, user_id: int) -> Awaitable[bool]: ...
