from dataclasses import replace
from pathlib import Path

from asyncpg import Connection  # pyright: ignore[reportMissingTypeStubs]
from pwdlib import PasswordHash

from app.constants.avatar import AVATAR_DIR
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import UserStats
from app.models.user import UserCreate, UserDB, UserStatus, UserUpdate
from app.repositories import user as UserRepo

from .errors import (
    UserAvatarNoneError,
    UserAvatarNotFoundError,
    UserNotCreateError,
    UserNotFoundError,
    UserNotUpdateError,
    UserUnauthorizedError,
)

password_hash = PasswordHash.recommended()


@trace(TraceLayer.SERVICE)
async def get_stats(
    conn: Connection,
    user_id: int,
) -> UserStats:
    return await UserRepo.get_stats(
        conn,
        user_id,
    )


@trace(TraceLayer.SERVICE)
async def getAvatar(conn: Connection, user_id: str) -> Path:
    user = await UserRepo.getByPublicId(conn, user_id)

    if user is None:
        raise UserNotFoundError()

    if user.avatar_key is None:
        raise UserAvatarNoneError()

    path = AVATAR_DIR / f"{user.avatar_key}.webp"

    if not path.is_file():
        raise UserAvatarNotFoundError()

    return path


@trace(TraceLayer.SERVICE)
async def getUserDB(conn: Connection, user_id: int, role_id: int | None) -> UserDB:
    user = await UserRepo.getById(conn, user_id)

    if user is None:
        raise UserNotFoundError()

    if role_id is not None and user.role_id != role_id:
        raise UserUnauthorizedError()

    return user


@trace(TraceLayer.SERVICE)
async def registerUser(conn: Connection, data: UserCreate):
    data = replace(data, password=password_hash.hash(data.password))

    id = await UserRepo.create(conn, data)

    if id is None:
        raise UserNotCreateError()


@trace(TraceLayer.SERVICE)
async def updateUser(conn: Connection, id: int, data: UserUpdate):
    if "password" in data.model_fields_set and data.password is not None:
        data = data.model_copy(update={"password": password_hash.hash(data.password)})

    result = await UserRepo.update(conn, id, data)

    if not result:
        raise UserNotUpdateError()


@trace(TraceLayer.SERVICE)
async def disableUser(conn: Connection, id: int):
    result = await UserRepo.update(conn, id, UserUpdate(status=UserStatus.DISACTIVE))

    if not result:
        raise UserNotUpdateError()


@trace(TraceLayer.SERVICE)
async def updateAvatar(
    conn: Connection, user_id: int, avatar_key: str | None
) -> str | None:
    avatar_key = await UserRepo.updateAvatar(conn, user_id, avatar_key)

    return avatar_key
