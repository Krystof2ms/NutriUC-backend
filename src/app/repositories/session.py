from app.core.config import TraceLayer
from app.core.database.interfaces import (
    DatabaseError,
    DatabaseInterface,
)
from app.core.decorator import trace
from app.models.session import SessionCreate, SessionDB
from app.repositories.interfaces.session import SessionRepositoryInterface

from .const import TablesName
from .errorrs import RepositoryError


class SessionRepository(SessionRepositoryInterface):
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @trace(TraceLayer.REPO)
    async def getByToken(self, jti: str) -> SessionDB | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"""
                    SELECT
                        id,
                        token_hash,
                        jti,
                        user_id,
                        expires_at,
                        revoked,
                        created_at
                    FROM {TablesName.SESSION}
                    WHERE jti = $1
                    """,
                    jti,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return SessionDB(**dict(row))

    @trace(TraceLayer.REPO)
    async def create(self, new: SessionCreate) -> int | None:
        async with self.db.connection() as conn:
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
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return row

    @trace(TraceLayer.REPO)
    async def revoked(self, id: int) -> bool:
        async with self.db.connection() as conn:
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
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return row_count > 0

    @trace(TraceLayer.REPO)
    async def revokedByJti(self, jti: str) -> bool:
        async with self.db.connection() as conn:
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
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return row_count > 0
