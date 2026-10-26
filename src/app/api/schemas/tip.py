from datetime import datetime

from pydantic import BaseModel, Field

from app.api.schemas.user import UserSummary
from app.models import CursorDirection
from app.models import tip as model


class TipBase(BaseModel):
    title: str
    content: str


class TipCreate(BaseModel):
    title: str
    content: str
    category: str

    def to_create(self) -> model.TipCreate:
        return model.TipCreate(
            title=self.title,
            content=self.content,
        )


class TipUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None

    def to_update(self, category_id: int | None = None) -> model.TipUpdate:
        data = self.model_dump(exclude_unset=True)

        if "category" in data:
            del data["category"]
            data["category_id"] = category_id

        return model.TipUpdate.model_construct(**data)


class TipDTO(TipBase):
    id: int
    category: str
    created_at: datetime
    owner: UserSummary


class TipQueryDTO(BaseModel):
    name: str | None = None
    category: str | None = None
    cursor: int | None = None
    limit: int = Field(default=12, gt=3, le=30)
    direction: CursorDirection = Field(alias="dir", default=CursorDirection.NEXT)
    mine: bool = False


TipCreateDTO = TipCreate
