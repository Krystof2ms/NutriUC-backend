from app.core.config import TraceLayer
from app.core.database.interfaces import (
    DatabaseError,
    DatabaseInterface,
)
from app.core.decorator import trace
from app.models.role import Role
from app.repositories.const import TablesName
from app.repositories.interfaces.role import RoleRepositoryInterface

from .errorrs import RepositoryError


class RoleRepository(RoleRepositoryInterface):
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @trace(TraceLayer.REPO)
    async def getAll(self) -> list[Role]:
        async with self.db.connection() as conn:
            try:
                rows = await conn.fetch(
                    f"\n            SELECT\n                id,\n                name,\n                created_at,\n                updated_at\n            FROM {TablesName.ROLE}\n            "
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            data = [Role(**dict(row)) for row in rows]
            return data
