from app.core.config import TraceLayer
from app.core.database.interfaces import (
    DatabaseError,
    DatabaseInterface,
)
from app.core.decorator import trace
from app.models.category import Category, CategoryType
from app.repositories.const import TablesName
from app.repositories.interfaces.category import CategoryRepositoryInterface

from .errorrs import RepositoryError


class CategoryRepository(CategoryRepositoryInterface):
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @trace(TraceLayer.REPO)
    async def getAll(self, *, only_type: CategoryType | None = None) -> list[Category]:
        async with self.db.connection() as conn:
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
            except DatabaseError as e:
                raise RepositoryError(error=e)
            data = [Category(**dict(row)) for row in rows]
            return data
