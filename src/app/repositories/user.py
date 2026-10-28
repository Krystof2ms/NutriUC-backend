# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from asyncpg import Connection, PostgresError  # pyright: ignore[reportMissingTypeStubs]

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import UserStats
from app.models.user import BaseUser, UserCreate, UserDB, UserUpdate

from .const import TablesName
from .errorrs import RepositoryError


@trace(TraceLayer.REPO)
async def get_stats(
    conn: Connection,
    user_id: int,
) -> UserStats:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT
                (
                    SELECT COUNT(*)
                    FROM {TablesName.RECIPE} r
                    WHERE r.user_id = $1
                ) AS recipes_count,
                (
                    SELECT COUNT(*)
                    FROM {TablesName.TIP} f
                    WHERE f.user_id = $1
                ) AS tips_count
            """,
            user_id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        raise RepositoryError(error=RuntimeError("Unable to retrieve user stats"))

    return UserStats(
        recipes_count=row["recipes_count"],
        tips_count=row["tips_count"],
    )


@trace(TraceLayer.REPO)
async def getByEmail(conn: Connection, email: str) -> UserDB | None:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT
                u.id,
                u.name,
                u.email,
                u.password_hash,
                u.status,
                r.name AS role,
                u.created_at,
                u.updated_at,
                u.avatar_key,
                u.public_id
            FROM {TablesName.USER} u
            INNER JOIN {TablesName.ROLE} r
                ON u.role_id = r.id
            WHERE u.email = $1
            """,
            email,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return UserDB(**dict(row))


@trace(TraceLayer.REPO)
async def getDTOById(conn: Connection, id: int) -> BaseUser | None:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT name, email, created_at, updated_at, public_id
                FROM {TablesName.USER} WHERE id = $1
            """,
            id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return BaseUser(**dict(row))


@trace(TraceLayer.REPO)
async def getByPublicId(conn: Connection, id: str) -> UserDB | None:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT
                u.id,
                u.name,
                u.email,
                u.password_hash,
                u.status,
                r.name AS role,
                u.created_at,
                u.updated_at,
                u.avatar_key,
                u.public_id
            FROM {TablesName.USER} u
            INNER JOIN {TablesName.ROLE} r
                ON u.role_id = r.id
            WHERE u.public_id = $1
            """,
            id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return UserDB(**dict(row))


@trace(TraceLayer.REPO)
async def getById(conn: Connection, id: int) -> UserDB | None:
    try:
        row = await conn.fetchrow(
            f"""
            SELECT
                u.id,
                u.name,
                u.email,
                u.password_hash,
                u.status,
                r.name AS role,
                u.created_at,
                u.updated_at,
                u.avatar_key,
                u.public_id
            FROM {TablesName.USER} u
            INNER JOIN {TablesName.ROLE} r
                ON u.role_id = r.id
            WHERE u.id = $1
            """,
            id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return UserDB(**dict(row))


@trace(TraceLayer.REPO)
async def create(conn: Connection, new: UserCreate) -> int | None:
    try:
        row = await conn.fetchval(
            f"""
            INSERT INTO {TablesName.USER} (name, email, password_hash, role_id) VALUES
            ($1, $2, $3, $4)
            RETURNING id;
            """,
            new.name,
            new.email,
            new.password,
            new.role_id,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    if row is None:
        return None

    return row


@trace(TraceLayer.REPO)
async def update(
    conn: Connection,
    user_id: int,
    data: UserUpdate,
) -> bool:
    values = data.model_dump(exclude_unset=True)

    if not values:
        return False

    set_parts = []
    params = []

    for index, (field, value) in enumerate(values.items(), start=1):  # pyright: ignore[reportAny]
        field = field if field != "password" else "password_hash"
        set_parts.append(f"{field} = ${index}")
        params.append(value)  # pyright: ignore[reportAny]

    params.append(user_id)
    user_id_param = len(params)

    try:
        status = await conn.execute(
            f"""
            UPDATE {TablesName.USER}
            SET {", ".join(set_parts)},
                updated_at = NOW()
            WHERE id = ${user_id_param}
            """,
            *params,
        )
    except PostgresError as e:
        raise RepositoryError(error=e)

    row_count = int(status.split()[-1])

    return bool(row_count)


@trace(TraceLayer.REPO)
async def updateAvatar(
    conn: Connection, user_id: int, avatar_key: str | None
) -> str | None:
    try:
        key = await conn.fetchval(
            f"""
            WITH old AS (
                SELECT avatar_key
                FROM {TablesName.USER}
                WHERE id = $2
            )
            UPDATE {TablesName.USER}
            SET avatar_key = $1,
                updated_at = NOW()
            WHERE id = $2
            RETURNING (SELECT avatar_key FROM old) AS old_avatar_key;
            """,
            avatar_key,
            user_id,
        )

        return key
    except PostgresError as e:
        raise RepositoryError(error=e)
