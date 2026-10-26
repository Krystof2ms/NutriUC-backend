from asyncpg import Connection

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.category import Category, CategoryType
from app.repositories import category as CategoryRepo


@trace(TraceLayer.SERVICE)
async def getAll(
    conn: Connection, only_type: CategoryType | None = None
) -> list[Category]:
    categories = await CategoryRepo.getAll(conn, only_type=only_type)

    return categories
