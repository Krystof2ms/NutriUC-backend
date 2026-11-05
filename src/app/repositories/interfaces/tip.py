from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.api.schemas.pagination import CursorPage
from app.models import CursorDirection, TipCreate, TipDTO, TipUpdate
from app.repositories.const import PAGE_SIZE


class TipRepositoryInterface(ABC):
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
    ) -> Awaitable[CursorPage[TipDTO] | None]: ...

    @abstractmethod
    def getDTO(self, id: int) -> Awaitable[TipDTO | None]: ...

    @abstractmethod
    def create(
        self, new: TipCreate, category_id: int, user_id: int
    ) -> Awaitable[int | None]: ...

    @abstractmethod
    def update(self, tip_id: int, user_id: int, data: TipUpdate) -> Awaitable[bool]: ...

    @abstractmethod
    def deleteById(self, recipe_id: int, user_id: int) -> Awaitable[bool]: ...
