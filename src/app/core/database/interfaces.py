from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any


class DatabaseError(Exception):
    """Database driver failure exposed without leaking driver types."""


class ConnectionInterface(ABC):
    @abstractmethod
    async def fetch(self, query: str, *args: Any) -> Sequence[Any]: ...

    @abstractmethod
    async def fetchrow(self, query: str, *args: Any) -> Any | None: ...

    @abstractmethod
    async def fetchval(self, query: str, *args: Any) -> Any: ...

    @abstractmethod
    async def execute(self, query: str, *args: Any) -> str: ...


class DatabaseInterface(ABC):
    @abstractmethod
    def connection(self) -> AbstractAsyncContextManager[ConnectionInterface]: ...
