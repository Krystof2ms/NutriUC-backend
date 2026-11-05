from dataclasses import asdict
from typing import Any

from app.api.schemas.pagination import CursorPage
from app.core.config import TraceLayer
from app.core.database.interfaces import (
    DatabaseError,
    DatabaseInterface,
)
from app.core.decorator import trace
from app.core.logger import logger
from app.models import CursorDirection, RecipeCreate, RecipeDB, RecipeDTO, RecipeUpdate
from app.repositories.interfaces.recipe import RecipeRepositoryInterface

from ..const import PAGE_SIZE, TablesName
from ..errorrs import RepositoryError
from . import utils


class RecipeRepository(RecipeRepositoryInterface):
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @trace(TraceLayer.REPO)
    async def getRecipeDB(self, id: int) -> RecipeDB | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n        SELECT id, name, origin, instructions, ingredients, description, category_id, user_id, image_key, updated_at, created_at\n            FROM {TablesName.RECIPE} WHERE id = $1\n        ",
                    id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return RecipeDB(**dict(row))

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
    ) -> CursorPage[RecipeDTO] | None:
        async with self.db.connection() as conn:
            conditions = []
            params = []
            if name:
                params.append(f"%{name}%")
                conditions.append(f'r."name" ILIKE ${len(params)}')
            if category:
                params.append(category)
                conditions.append(f'c."name" = ${len(params)}')
            if user_id:
                params.append(user_id)
                conditions.append(f"r.user_id = ${len(params)}")
            base_conditions = conditions.copy()
            base_params = params.copy()
            if cursor is not None:
                params.append(cursor)
                conditions.append(f"r.id {direction.sql_operator} ${len(params)}")
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            params.append(limit + 1)
            limit_param = len(params)
            try:
                rows: list[Any] = list(
                    await conn.fetch(
                        f"\n            SELECT\n                r.id,\n                r.name,\n                r.origin,\n                r.instructions,\n                r.ingredients,\n                r.description,\n                r.created_at,\n                r.user_id,\n                r.image_key IS NOT NULL AS has_image,\n                c.name AS category,\n                u.public_id AS owner_id,\n                u.name AS owner_name,\n                u.avatar_key IS NOT NULL AS owner_avatar\n            FROM {TablesName.RECIPE} r\n            INNER JOIN {TablesName.CATEGORY} c\n                ON r.category_id = c.id\n            INNER JOIN {TablesName.USER} u\n                ON r.user_id = u.id\n            {where}\n            ORDER BY r.id {direction.sql_order}\n            LIMIT ${limit_param}\n            ",
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
    async def getDTO(self, id: int) -> RecipeDTO | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n            SELECT\n                r.id,\n                r.name,\n                r.origin,\n                r.instructions,\n                r.ingredients,\n                r.description,\n                r.created_at,\n                r.updated_at,\n                r.user_id,\n                r.image_key IS NOT NULL AS has_image,\n                c.name AS category,\n                u.public_id AS owner_id,\n                u.name AS owner_name,\n                u.avatar_key IS NOT NULL owner_avatar\n            FROM {TablesName.RECIPE} r\n            INNER JOIN {TablesName.CATEGORY} c\n                ON r.category_id = c.id\n            INNER JOIN {TablesName.USER} u\n                ON r.user_id = u.id\n            WHERE\n                r.id = $1\n            ",
                    id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return utils.parser_dto(row)

    @trace(TraceLayer.REPO)
    async def create(
        self, new: RecipeCreate, category_id: int, user_id: int
    ) -> int | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchval(
                    f"\n            INSERT INTO {TablesName.RECIPE} (\n                name,\n                origin,\n                instructions,\n                ingredients,\n                description,\n                category_id,\n                image_key,\n                user_id\n            )\n            VALUES (\n                $1, $2, $3, $4,\n                $5, $6, $7, $8\n            )\n            RETURNING id;\n            ",
                    new.name,
                    new.origin,
                    [asdict(instruction) for instruction in new.instructions],
                    [asdict(ingredient) for ingredient in new.ingredients],
                    new.description,
                    category_id,
                    new.image_key,
                    user_id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return row

    @trace(TraceLayer.REPO)
    async def update(self, recipe_id: int, user_id: int, data: RecipeUpdate) -> bool:
        async with self.db.connection() as conn:
            values = data.model_dump(exclude_unset=True)
            set_parts = []
            params = []
            if not values:
                return False
            for index, (field, value) in enumerate(values.items(), start=1):
                set_parts.append(f"{field} = ${index}")
                params.append(value)
            params.append(recipe_id)
            params.append(user_id)
            id_param = len(params) - 1
            user_id_param = id_param + 1
            logger.debug(params)
            try:
                status = await conn.execute(
                    f"\n            UPDATE {TablesName.RECIPE}\n            SET\n                {', '.join(set_parts)},\n                updated_at = NOW()\n            WHERE id = ${id_param} AND user_id = ${user_id_param}\n            ",
                    *params,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return row_count > 0

    @trace(TraceLayer.REPO)
    async def updateImage(
        self, id: int, user_id: int, image_key: str | None
    ) -> str | None:
        async with self.db.connection() as conn:
            try:
                key = await conn.fetchval(
                    f"\n            WITH old AS (\n                SELECT image_key\n                FROM {TablesName.RECIPE}\n                WHERE id = $2 AND user_id = $3\n            )\n            UPDATE {TablesName.RECIPE}\n            SET\n                image_key = $1,\n                updated_at = NOW()\n            WHERE id = $2 AND user_id = $3\n            ",
                    image_key,
                    id,
                    user_id,
                )
                return key
            except DatabaseError as e:
                raise RepositoryError(error=e)

    @trace(TraceLayer.REPO)
    async def deleteById(self, recipe_id: int, user_id: int) -> bool:
        async with self.db.connection() as conn:
            try:
                status = await conn.execute(
                    f"\n            DELETE FROM {TablesName.RECIPE}\n                WHERE id = $1 AND user_id = $2\n            ",
                    recipe_id,
                    user_id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return row_count > 0
