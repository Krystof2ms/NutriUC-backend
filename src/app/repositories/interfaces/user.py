from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.models import UserStats
from app.models.user import BaseUser, UserCreate, UserDB, UserUpdate


class UserRepositoryInterface(ABC):
    @abstractmethod
    def get_stats(self, user_id: int) -> Awaitable[UserStats]: ...

    @abstractmethod
    def getByEmail(self, email: str) -> Awaitable[UserDB | None]: ...

    @abstractmethod
    def getDTOById(self, id: int) -> Awaitable[BaseUser | None]: ...

    @abstractmethod
    def getByPublicId(self, id: str) -> Awaitable[UserDB | None]: ...

    @abstractmethod
    def getById(self, id: int) -> Awaitable[UserDB | None]: ...

    @abstractmethod
    def create(self, new: UserCreate) -> Awaitable[int | None]: ...

    @abstractmethod
    def update(self, user_id: int, data: UserUpdate) -> Awaitable[bool]: ...

    @abstractmethod
    def updateAvatar(
        self, user_id: int, avatar_key: str | None
    ) -> Awaitable[str | None]: ...
