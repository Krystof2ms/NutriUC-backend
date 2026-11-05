from typing import Any

from app.api.schemas.pagination import CursorPage
from app.core.config import TraceLayer
from app.core.database.interfaces import (
    DatabaseError,
    DatabaseInterface,
)
from app.core.decorator import trace
from app.models import CursorDirection, TipCreate, TipDTO, TipUpdate
from app.repositories.const import PAGE_SIZE, TablesName
from app.repositories.errorrs import RepositoryError
from app.repositories.interfaces.tip import TipRepositoryInterface

from . import utils


class TipRepository(TipRepositoryInterface):
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @trace(TraceLayer.REPO)
    async def getDtoWithParams(
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        user_id: int | None = None,
        cursor: int | None = None,
        limit: int = PAGE_SIZE,
        direction: CursorDirection = CursorDirection.NEXT,
    ) -> CursorPage[TipDTO] | None:
        async with self.db.connection() as conn:
            conditions = []
            params = []
            if name:
                params.append(f"%{name}%")
                conditions.append(f't."title" ILIKE ${len(params)}')
            if category:
                params.append(category)
                conditions.append(f'c."name" = ${len(params)}')
            if user_id:
                params.append(user_id)
                conditions.append(f"t.user_id = ${len(params)}")
            base_conditions = conditions.copy()
            base_params = params.copy()
            if cursor is not None:
                params.append(cursor)
                conditions.append(f"t.id {direction.sql_operator} ${len(params)}")
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            params.append(limit + 1)
            limit_param = len(params)
            try:
                rows: list[Any] = list(
                    await conn.fetch(
                        f"\n            SELECT\n                t.id,\n                t.title,\n                t.content,\n                t.created_at,\n                t.updated_at,\n                t.user_id,\n                c.id AS category_id,\n                c.name AS category,\n                u.public_id AS owner_id,\n                u.name AS owner_name,\n                u.avatar_key IS NOT NULL AS owner_avatar\n            FROM {TablesName.TIP} t\n            INNER JOIN {TablesName.CATEGORY} c\n                ON t.category_id = c.id\n            INNER JOIN {TablesName.USER} u\n                ON t.user_id = u.id\n            {where}\n            ORDER BY t.id {direction.sql_order}\n            LIMIT ${limit_param}\n            ",
                        *params,
                    )
                )
                if len(rows) == 0:
                    return None
                has_more = len(rows) > limit
                if has_more:
                    rows = rows[:limit]
                if direction is CursorDirection.PREVIOUS:
                    rows.reverse()
                previous_cursor = None
                if cursor is not None:
                    first_id = rows[0]["id"]
                    previous_params = [*base_params, first_id]
                    previous_conditions = [
                        *base_conditions,
                        f"r.id < ${len(previous_params)}",
                    ]
                    previous_where = f"WHERE {' AND '.join(previous_conditions)}"
                    has_previous = await conn.fetchval(
                        f"\n                    SELECT EXISTS (\n                        SELECT 1\n                        FROM {TablesName.RECIPE} r\n                        INNER JOIN {TablesName.CATEGORY} c\n                            ON r.category_id = c.id\n                        {previous_where}\n                    )\n                ",
                        *previous_params,
                    )
                    previous_cursor = first_id if has_previous else None
            except DatabaseError as e:
                raise RepositoryError(error=e)
            data = [utils.parser_dto(row) for row in rows]
            if direction is CursorDirection.NEXT:
                next_cursor = rows[-1]["id"] if has_more else None
            else:
                next_cursor = rows[-1]["id"]
            return CursorPage(
                data=data, next_cursor=next_cursor, previous_cursor=previous_cursor
            )

    @trace(TraceLayer.REPO)
    async def getDTO(self, id: int) -> TipDTO | None:
        async with self.db.connection() as conn:
            try:
                row: Any | None = await conn.fetchrow(
                    f"\n            SELECT\n                t.id,\n                t.title,\n                t.content,\n                t.created_at,\n                t.updated_at,\n                t.user_id,\n                c.id AS category_id,\n                c.name AS category,\n                u.public_id AS owner_id,\n                u.name AS owner_name,\n                u.avatar_key IS NOT NULL AS owner_avatar\n            FROM {TablesName.TIP} t\n            INNER JOIN {TablesName.CATEGORY} c\n                ON t.category_id = c.id\n            INNER JOIN {TablesName.USER} u\n                ON t.user_id = u.id\n            WHERE\n                t.id = $1\n            ",
                    id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return utils.parser_dto(row)

    @trace(TraceLayer.REPO)
    async def create(
        self, new: TipCreate, category_id: int, user_id: int
    ) -> int | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchval(
                    f"\n            INSERT INTO {TablesName.TIP} (\n                title,\n                content,\n                category_id,\n                user_id\n            )\n            VALUES (\n                $1, $2, $3, $4\n            )\n            RETURNING id;\n            ",
                    new.title,
                    new.content,
                    category_id,
                    user_id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return row

    @trace(TraceLayer.REPO)
    async def update(self, tip_id: int, user_id: int, data: TipUpdate) -> bool:
        async with self.db.connection() as conn:
            values = data.model_dump(exclude_unset=True)
            if not values:
                return False
            set_parts = []
            params = []
            for index, (field, value) in enumerate(values.items(), start=1):
                set_parts.append(f"{field} = ${index}")
                params.append(value)
            params.append(tip_id)
            params.append(user_id)
            id_param = len(params) - 1
            user_id_param = id_param + 1
            try:
                status = await conn.execute(
                    f"\n            UPDATE {TablesName.TIP}\n            SET\n                {', '.join(set_parts)},\n                updated_at = NOW()\n            WHERE id = ${id_param} AND user_id = ${user_id_param}\n            ",
                    *params,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return row_count > 0

    @trace(TraceLayer.REPO)
    async def deleteById(self, recipe_id: int, user_id: int) -> bool:
        async with self.db.connection() as conn:
            try:
                status = await conn.execute(
                    f"\n            DELETE FROM {TablesName.TIP}\n                WHERE id = $1 AND user_id = $2\n            ",
                    recipe_id,
                    user_id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return row_count > 0
