# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from asyncpg import Connection, PostgresError  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.role import Role
from app.repositories.const import TablesName

from .errorrs import RepositoryError


@trace(TraceLayer.REPO)
async def getAll(conn: Connection) -> list[Role]:
    try:
        rows = await conn.fetch(
            f"""
            SELECT
                id,
                name,
                created_at,
                updated_at
            FROM {TablesName.ROLE}
            """
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    data = [Role(**dict(row)) for row in rows]

    return data
