import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import TraceLayer, settings
from app.core.database.interfaces import ConnectionInterface, DatabaseInterface
from app.core.database.postgres.connection import PostgresConnection
from app.core.logger import init_logger as logger_core


class PostgresDatabase(DatabaseInterface):
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[ConnectionInterface]:
        async with self._pool.acquire() as connection:
            yield PostgresConnection(connection)

    @classmethod
    async def create_pool(cls) -> Any:
        query_logger: logging.Logger | None = None
        if (
            TraceLayer.DB in settings.TRACE_LAYERS
            and settings.FASTAPI_ENV == "development"
        ):
            query_logger = logger_core("sql")

        async def initialize(connection: Any) -> None:
            await connection.set_type_codec(
                "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
            )
            await connection.set_type_codec(
                "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
            )
            if query_logger is not None:
                active_logger = query_logger

                def log_query(record: Any) -> None:
                    active_logger.debug(
                        "SQL: %s | ARGS: %s | %.2f ms",
                        record.query,
                        record.args,
                        record.elapsed * 1000,
                    )

                connection.add_query_logger(log_query)

        return await asyncpg.create_pool(str(settings.DATABASE_URL), init=initialize)
