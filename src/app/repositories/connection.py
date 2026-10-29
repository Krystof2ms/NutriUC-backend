import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Protocol

import asyncpg  # pyright: ignore[reportMissingTypeStubs]
from asyncpg.pool import PoolConnectionProxy  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import TraceLayer, settings
from app.core.logger import init_logger as logger_core


class QueryLogRecord(Protocol):
    query: str
    elapsed: float


pool: asyncpg.Pool


def init_logger(logger: logging.Logger):
    def pg_query_logger(record: QueryLogRecord) -> None:
        logger.debug(
            "SQL: %s | ARGS: %s | %.2f ms",
            record.query,
            record.args,
            record.elapsed * 1000,
        )

    return pg_query_logger


async def connect() -> asyncpg.Pool:
    global pool

    logger = None

    if TraceLayer.DB in settings.TRACE_LAYERS and settings.FASTAPI_ENV == "development":
        logger = logger_core("sql")

    async def init_connection(conn: asyncpg.Connection) -> None:
        await conn.set_type_codec(  # pyright: ignore[reportUnknownMemberType]
            "json",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

        await conn.set_type_codec(  # pyright: ignore[reportUnknownMemberType]
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

        if logger is not None:
            conn.add_query_logger(init_logger(logger))  # pyright: ignore[reportUnknownMemberType]

    pool = await asyncpg.create_pool(  # pyright: ignore[reportUnknownMemberType]
        str(settings.DATABASE_URL),
        init=init_connection,
    )

    return pool


async def get_db() -> AsyncGenerator[PoolConnectionProxy]:
    async with pool.acquire() as connection:  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        yield connection


async def close():
    await pool.close()


@asynccontextmanager
async def db_connection() -> AsyncGenerator[PoolConnectionProxy]:
    async with pool.acquire() as connection:
        yield connection
