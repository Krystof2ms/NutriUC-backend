from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserSummary


@dataclass(frozen=True, kw_only=True)
class TipBase:
    title: str
    content: str


@dataclass(frozen=True, kw_only=True)
class TipCreate(TipBase):
    pass


@dataclass(frozen=True, kw_only=True)
class TipDB(TipCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class TipUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category_id: int | None = None


@dataclass(frozen=True, kw_only=True)
class TipDTO(TipBase):
    id: int
    category: str
    created_at: datetime
    owner: UserSummary

    @classmethod
    def from_base(
        cls,
        base: TipBase,
        *,
        id: int,
        category: str,
        created_at: datetime,
        owner: UserSummary,
    ) -> TipDTO:
        return cls(
            id=id,
            title=base.title,
            content=base.content,
            category=category,
            created_at=created_at,
            owner=owner,
        )
