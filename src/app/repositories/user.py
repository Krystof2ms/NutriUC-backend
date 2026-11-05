from app.core.config import TraceLayer
from app.core.database.interfaces import (
    DatabaseError,
    DatabaseInterface,
)
from app.core.decorator import trace
from app.models import UserStats
from app.models.user import BaseUser, UserCreate, UserDB, UserUpdate
from app.repositories.interfaces.user import UserRepositoryInterface

from .const import TablesName
from .errorrs import RepositoryError


class UserRepository(UserRepositoryInterface):
    def __init__(self, db: DatabaseInterface):
        self.db = db

    @trace(TraceLayer.REPO)
    async def get_stats(self, user_id: int) -> UserStats:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n            SELECT\n                (\n                    SELECT COUNT(*)\n                    FROM {TablesName.RECIPE} r\n                    WHERE r.user_id = $1\n                ) AS recipes_count,\n                (\n                    SELECT COUNT(*)\n                    FROM {TablesName.TIP} f\n                    WHERE f.user_id = $1\n                ) AS tips_count\n            ",
                    user_id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                raise RepositoryError(
                    error=RuntimeError("Unable to retrieve user stats")
                )
            return UserStats(
                recipes_count=row["recipes_count"], tips_count=row["tips_count"]
            )

    @trace(TraceLayer.REPO)
    async def getByEmail(self, email: str) -> UserDB | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n            SELECT\n                u.id,\n                u.name,\n                u.email,\n                u.password_hash,\n                u.status,\n                r.name AS role,\n                u.created_at,\n                u.updated_at,\n                u.avatar_key,\n                u.public_id\n            FROM {TablesName.USER} u\n            INNER JOIN {TablesName.ROLE} r\n                ON u.role_id = r.id\n            WHERE u.email = $1\n            ",
                    email,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return UserDB(**dict(row))

    @trace(TraceLayer.REPO)
    async def getDTOById(self, id: int) -> BaseUser | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n            SELECT name, email, created_at, updated_at, public_id\n                FROM {TablesName.USER} WHERE id = $1\n            ",
                    id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return BaseUser(**dict(row))

    @trace(TraceLayer.REPO)
    async def getByPublicId(self, id: str) -> UserDB | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n            SELECT\n                u.id,\n                u.name,\n                u.email,\n                u.password_hash,\n                u.status,\n                r.name AS role,\n                u.created_at,\n                u.updated_at,\n                u.avatar_key,\n                u.public_id\n            FROM {TablesName.USER} u\n            INNER JOIN {TablesName.ROLE} r\n                ON u.role_id = r.id\n            WHERE u.public_id = $1\n            ",
                    id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return UserDB(**dict(row))

    @trace(TraceLayer.REPO)
    async def getById(self, id: int) -> UserDB | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchrow(
                    f"\n            SELECT\n                u.id,\n                u.name,\n                u.email,\n                u.password_hash,\n                u.status,\n                r.name AS role,\n                u.created_at,\n                u.updated_at,\n                u.avatar_key,\n                u.public_id\n            FROM {TablesName.USER} u\n            INNER JOIN {TablesName.ROLE} r\n                ON u.role_id = r.id\n            WHERE u.id = $1\n            ",
                    id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return UserDB(**dict(row))

    @trace(TraceLayer.REPO)
    async def create(self, new: UserCreate) -> int | None:
        async with self.db.connection() as conn:
            try:
                row = await conn.fetchval(
                    f"\n            INSERT INTO {TablesName.USER} (name, email, password_hash, role_id) VALUES\n            ($1, $2, $3, $4)\n            RETURNING id;\n            ",
                    new.name,
                    new.email,
                    new.password,
                    new.role_id,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            if row is None:
                return None
            return row

    @trace(TraceLayer.REPO)
    async def update(self, user_id: int, data: UserUpdate) -> bool:
        async with self.db.connection() as conn:
            values = data.model_dump(exclude_unset=True)
            if not values:
                return False
            set_parts = []
            params = []
            for index, (field, value) in enumerate(values.items(), start=1):
                field = field if field != "password" else "password_hash"
                set_parts.append(f"{field} = ${index}")
                params.append(value)
            params.append(user_id)
            user_id_param = len(params)
            try:
                status = await conn.execute(
                    f"\n            UPDATE {TablesName.USER}\n            SET {', '.join(set_parts)},\n                updated_at = NOW()\n            WHERE id = ${user_id_param}\n            ",
                    *params,
                )
            except DatabaseError as e:
                raise RepositoryError(error=e)
            row_count = int(status.split()[-1])
            return bool(row_count)

    @trace(TraceLayer.REPO)
    async def updateAvatar(self, user_id: int, avatar_key: str | None) -> str | None:
        async with self.db.connection() as conn:
            try:
                key = await conn.fetchval(
                    f"\n            WITH old AS (\n                SELECT avatar_key\n                FROM {TablesName.USER}\n                WHERE id = $2\n            )\n            UPDATE {TablesName.USER}\n            SET avatar_key = $1,\n                updated_at = NOW()\n            WHERE id = $2\n            RETURNING (SELECT avatar_key FROM old) AS old_avatar_key;\n            ",
                    avatar_key,
                    user_id,
                )
                return key
            except DatabaseError as e:
                raise RepositoryError(error=e)
