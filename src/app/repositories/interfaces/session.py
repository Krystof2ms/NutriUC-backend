from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable

from app.models.session import SessionCreate, SessionDB


class SessionRepositoryInterface(ABC):
    @abstractmethod
    def getByToken(self, jti: str) -> Awaitable[SessionDB | None]: ...

    @abstractmethod
    def create(self, new: SessionCreate) -> Awaitable[int | None]: ...

    @abstractmethod
    def revoked(self, id: int) -> Awaitable[bool]: ...

    @abstractmethod
    def revokedByJti(self, jti: str) -> Awaitable[bool]: ...
