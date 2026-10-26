# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from asyncpg import Connection, PostgresError  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.category import Category, CategoryType
from app.repositories.const import TablesName

from .errorrs import RepositoryError


@trace(TraceLayer.REPO)
async def getAll(
    conn: Connection, *, only_type: CategoryType | None = None
) -> list[Category]:

    where = ""

    if only_type is not None:
        where = "WHERE type = $1"

    try:
        rows = await conn.fetch(
            f"""
            SELECT
                id,
                name,
                description,
                type
            FROM {TablesName.CATEGORY}
            {where}
            """,
            *([only_type] if only_type is not None else []),
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    data = [Category(**dict(row)) for row in rows]

    return data
