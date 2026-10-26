# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from asyncpg import Connection, PostgresError  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.session import SessionCreate, SessionDB

from .const import TablesName
from .errorrs import RepositoryError


@trace(TraceLayer.REPO)
async def getByToken(conn: Connection, jti: str) -> SessionDB | None:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT id, token_hash, jti, user_id, expires_at, revoked, created_at FROM {TablesName.SESSION}
            WHERE jti = $1
            """,
            jti,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return SessionDB(**dict(row))


@trace(TraceLayer.REPO)
async def create(conn: Connection, new: SessionCreate) -> int | None:
    try:
        row = await conn.fetchval(
            f"""
            INSERT INTO {TablesName.SESSION}
                (token_hash, user_id, expires_at, jti)
            VALUES
                ($1, $2, $3, $4)
            RETURNING id;
            """,
            new.token_hash,
            new.user_id,
            new.expires_at,
            new.jti,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return row


@trace(TraceLayer.REPO)
async def revoked(conn: Connection, id: int) -> bool:
    try:
        status = await conn.execute(
            f"""
            UPDATE {TablesName.SESSION}
            SET
                revoked = true
            WHERE id = $1
            """,
            id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    row_count = int(status.split()[-1])

    return row_count > 0


@trace(TraceLayer.REPO)
async def revokedByJti(conn: Connection, jti: str) -> bool:
    try:
        status = await conn.execute(
            f"""
            UPDATE {TablesName.SESSION}
            SET
                revoked = true
            WHERE jti = $1
            """,
            jti,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    row_count = int(status.split()[-1])

    return row_count > 0
