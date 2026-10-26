from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.jobs.user import Crop as CropModel
from app.models import user as model


class UserSummary(BaseModel):
    public_id: UUID
    name: str
    has_image: bool


class BaseUser(BaseModel):
    email: EmailStr
    created_at: datetime
    public_id: UUID
    name: str


class UserSummaryMe(UserSummary):
    email: str
    created_at: datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=20)

    def to_create(self, role_id: int) -> model.UserCreate:
        return model.UserCreate(
            role_id=role_id,
            name=self.name,
            email=str(self.email),
            password=self.password,
        )


class Crop(BaseModel):
    x: float = Field(ge=0, lt=1)
    y: float = Field(ge=0, lt=1)
    size: float = Field(gt=0, le=1)

    def to_crop(self) -> CropModel:
        return CropModel(x=self.x, y=self.y, size=self.size)


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None

    def to_update(self) -> model.UserUpdate:
        data = self.model_dump(exclude_unset=True)

        return model.UserUpdate(**data)


UserCreateDTO = UserCreate


class UserStats(BaseModel):
    recipes_count: int
    tips_count: int
