from typing import Any

import asyncpg  # pyright: ignore[reportMissingTypeStubs]

from app.core.database.interfaces import ConnectionInterface, DatabaseError


class PostgresConnection(ConnectionInterface):
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    async def fetch(self, query: str, *args: Any):
        try:
            return await self._connection.fetch(query, *args)
        except asyncpg.PostgresError as error:
            raise DatabaseError(str(error)) from error

    async def fetchrow(self, query: str, *args: Any):
        try:
            return await self._connection.fetchrow(query, *args)
        except asyncpg.PostgresError as error:
            raise DatabaseError(str(error)) from error

    async def fetchval(self, query: str, *args: Any):
        try:
            return await self._connection.fetchval(query, *args)
        except asyncpg.PostgresError as error:
            raise DatabaseError(str(error)) from error

    async def execute(self, query: str, *args: Any) -> str:
        try:
            return await self._connection.execute(query, *args)
        except asyncpg.PostgresError as error:
            raise DatabaseError(str(error)) from error
