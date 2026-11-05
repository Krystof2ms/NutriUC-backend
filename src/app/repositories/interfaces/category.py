from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.models.category import Category, CategoryType


class CategoryRepositoryInterface(ABC):
    @abstractmethod
    def getAll(
        self, *, only_type: CategoryType | None = None
    ) -> Awaitable[list[Category]]: ...
