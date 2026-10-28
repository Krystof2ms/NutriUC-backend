# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

import json
from dataclasses import asdict

from asyncpg import (  # pyright: ignore[reportMissingTypeStubs]
    Connection,
    PostgresError,
    Record,
)

from app.api.schemas.pagination import CursorPage
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.core.logger import logger
from app.models import CursorDirection, RecipeCreate, RecipeDB, RecipeDTO, RecipeUpdate

from ..const import PAGE_SIZE, TablesName
from ..errorrs import RepositoryError
from . import utils


@trace(TraceLayer.REPO)
async def getRecipeDB(conn: Connection, id: int) -> RecipeDB | None:
    try:
        row = await conn.fetchrow(
            f"""
        SELECT id, name, origin, instructions, ingredients, description, category_id, user_id, image_key, updated_at, created_at
            FROM {TablesName.RECIPE} WHERE id = $1
        """,
            id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return RecipeDB(**dict(row))


@trace(TraceLayer.REPO)
async def getDtoWithParams(
    conn: Connection,
    *,
    name: str | None = None,
    category: str | None = None,
    user_id: int | None = None,
    cursor: int | None = None,
    limit: int = PAGE_SIZE,
    direction: CursorDirection = CursorDirection.NEXT,
) -> CursorPage[RecipeDTO] | None:

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

    # Pedimos uno extra para saber si existen más.
    params.append(limit + 1)
    limit_param = len(params)

    try:
        rows: list[Record] = await conn.fetch(
            f"""
            SELECT
                r.id,
                r.name,
                r.origin,
                r.instructions,
                r.ingredients,
                r.description,
                r.created_at,
                r.user_id,
                r.image_key IS NOT NULL AS has_image,
                c.name AS category,
                u.public_id AS owner_id,
                u.name AS owner_name,
                u.avatar_key IS NOT NULL AS owner_avatar
            FROM {TablesName.RECIPE} r
            INNER JOIN {TablesName.CATEGORY} c
                ON r.category_id = c.id
            INNER JOIN {TablesName.USER} u
                ON r.user_id = u.id
            {where}
            ORDER BY r.id {direction.sql_order}
            LIMIT ${limit_param}
            """,
            *params,
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
                f"""
                    SELECT EXISTS (
                        SELECT 1
                        FROM {TablesName.RECIPE} r
                        INNER JOIN {TablesName.CATEGORY} c
                            ON r.category_id = c.id
                        {previous_where}
                    )
                """,
                *previous_params,
            )

            previous_cursor = first_id if has_previous else None

    except PostgresError as e:
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
async def getDTO(conn: Connection, id: int) -> RecipeDTO | None:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT
                r.id,
                r.name,
                r.origin,
                r.instructions,
                r.ingredients,
                r.description,
                r.created_at,
                r.updated_at,
                r.user_id,
                r.image_key IS NOT NULL AS has_image,
                c.name AS category,
                u.public_id AS owner_id,
                u.name AS owner_name,
                u.avatar_key IS NOT NULL owner_avatar
            FROM {TablesName.RECIPE} r
            INNER JOIN {TablesName.CATEGORY} c
                ON r.category_id = c.id
            INNER JOIN {TablesName.USER} u
                ON r.user_id = u.id
            WHERE
                r.id = $1
            """,
            id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return utils.parser_dto(row)


@trace(TraceLayer.REPO)
async def create(
    conn: Connection,
    new: RecipeCreate,
    category_id: int,
    user_id: int,
) -> int | None:
    try:
        row = await conn.fetchval(
            f"""
            INSERT INTO {TablesName.RECIPE} (
                name,
                origin,
                instructions,
                ingredients,
                description,
                category_id,
                image_key,
                user_id
            )
            VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8
            )
            RETURNING id;
            """,
            new.name,
            new.origin,
            [asdict(instruction) for instruction in new.instructions],
            [asdict(ingredient) for ingredient in new.ingredients],
            new.description,
            category_id,
            new.image_key,
            user_id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return row


@trace(TraceLayer.REPO)
async def update(
    conn: Connection,
    recipe_id: int,
    user_id: int,
    data: RecipeUpdate,
) -> bool:
    values = data.model_dump(exclude_unset=True)

    set_parts = []
    params = []

    if not values:
        return False

    for index, (field, value) in enumerate(values.items(), start=1):  # pyright: ignore[reportAny]
        set_parts.append(f"{field} = ${index}")  # TODO: fix case json
        params.append(value)  # pyright: ignore[reportAny]

    params.append(recipe_id)
    params.append(user_id)
    id_param = len(params) - 1
    user_id_param = id_param + 1

    logger.debug(params)

    try:
        status = await conn.execute(
            f"""
            UPDATE {TablesName.RECIPE}
            SET
                {", ".join(set_parts)},
                updated_at = NOW()
            WHERE id = ${id_param} AND user_id = ${user_id_param}
            """,
            *params,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    row_count = int(status.split()[-1])

    return row_count > 0


@trace(TraceLayer.REPO)
async def updateImage(
    conn: Connection, id: int, user_id: int, image_key: str | None
) -> str | None:
    try:
        key = await conn.fetchval(
            f"""
            WITH old AS (
                SELECT image_key
                FROM {TablesName.RECIPE}
                WHERE id = $2 AND user_id = $3
            )
            UPDATE {TablesName.RECIPE}
            SET
                image_key = $1,
                updated_at = NOW()
            WHERE id = $2 AND user_id = $3
            """,
            image_key,
            id,
            user_id,
        )

        return key
    except PostgresError as e:
        raise RepositoryError(error=e)


@trace(TraceLayer.REPO)
async def deleteById(conn: Connection, recipe_id: int, user_id: int) -> bool:
    try:
        status = await conn.execute(
            f"""
            DELETE FROM {TablesName.RECIPE}
                WHERE id = $1 AND user_id = $2
            """,
            recipe_id,
            user_id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    row_count = int(status.split()[-1])

    return row_count > 0
