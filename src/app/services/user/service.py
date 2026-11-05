from dataclasses import replace
from pathlib import Path

from pwdlib import PasswordHash

from app.constants.avatar import AVATAR_DIR
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import UserStats
from app.models.user import UserCreate, UserDB, UserStatus, UserUpdate
from app.repositories.interfaces.user import UserRepositoryInterface

from .errors import (
    UserAvatarNoneError,
    UserAvatarNotFoundError,
    UserNotCreateError,
    UserNotFoundError,
    UserNotUpdateError,
    UserUnauthorizedError,
)

password_hash = PasswordHash.recommended()


class UserService:
    def __init__(self, user_repo: UserRepositoryInterface):
        self.user_repo = user_repo

    @trace(TraceLayer.SERVICE)
    async def get_stats(self, user_id: int) -> UserStats:
        return await self.user_repo.get_stats(user_id)

    @trace(TraceLayer.SERVICE)
    async def getAvatar(self, user_id: str) -> Path:
        user = await self.user_repo.getByPublicId(user_id)
        if user is None:
            raise UserNotFoundError()
        if user.avatar_key is None:
            raise UserAvatarNoneError()
        path = AVATAR_DIR / f"{user.avatar_key}.webp"
        if not path.is_file():
            raise UserAvatarNotFoundError()
        return path

    @trace(TraceLayer.SERVICE)
    async def getUserDB(self, user_id: int, role: str | None = None) -> UserDB:
        user = await self.user_repo.getById(user_id)
        if user is None:
            raise UserNotFoundError()
        if role is not None and user.role != role:
            raise UserUnauthorizedError()
        return user

    @trace(TraceLayer.SERVICE)
    async def registerUser(self, data: UserCreate):
        data = replace(data, password=password_hash.hash(data.password))
        id = await self.user_repo.create(data)
        if id is None:
            raise UserNotCreateError()

    @trace(TraceLayer.SERVICE)
    async def updateUser(self, id: int, data: UserUpdate):
        if "password" in data.model_fields_set and data.password is not None:
            data = data.model_copy(
                update={"password": password_hash.hash(data.password)}
            )
        result = await self.user_repo.update(id, data)
        if not result:
            raise UserNotUpdateError()

    @trace(TraceLayer.SERVICE)
    async def disableUser(self, id: int):
        result = await self.user_repo.update(
            id, UserUpdate(status=UserStatus.DISACTIVE)
        )
        if not result:
            raise UserNotUpdateError()

    @trace(TraceLayer.SERVICE)
    async def updateAvatar(self, user_id: int, avatar_key: str | None) -> str | None:
        avatar_key = await self.user_repo.updateAvatar(user_id, avatar_key)
        return avatar_key
