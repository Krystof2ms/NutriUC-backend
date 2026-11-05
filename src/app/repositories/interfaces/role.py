from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.models.role import Role


class RoleRepositoryInterface(ABC):
    @abstractmethod
    def getAll(self) -> Awaitable[list[Role]]: ...
