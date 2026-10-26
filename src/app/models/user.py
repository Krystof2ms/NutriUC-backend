from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISACTIVE = "disactive"


@dataclass(frozen=True, kw_only=True)
class UserSummary:
    public_id: UUID
    has_image: bool
    name: str


@dataclass(frozen=True, kw_only=True)
class UserSummaryMe(UserSummary):
    email: str
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class BaseUser:
    email: str
    created_at: datetime
    public_id: UUID
    name: str


@dataclass(frozen=True, kw_only=True)
class UserCreate:
    role_id: int
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    avatar_key: str | None = None
    password: str | None = None
    status: UserStatus | None = None


@dataclass(frozen=True, kw_only=True)
class UserDB(BaseUser):
    id: str
    role_id: int
    status: UserStatus
    password_hash: str | None
    avatar_key: str | None
    updated_at: datetime

    def to_base(self) -> BaseUser:
        return BaseUser(
            public_id=self.public_id,
            name=self.name,
            email=self.email,
            created_at=self.created_at,
        )

    def to_summary_me(self) -> UserSummaryMe:
        return UserSummaryMe(
            public_id=self.public_id,
            name=self.name,
            email=self.email,
            created_at=self.created_at,
            has_image=self.avatar_key is not None
        )


@dataclass(frozen=True, kw_only=True)
class UserStats:
    recipes_count: int
    tips_count: int
