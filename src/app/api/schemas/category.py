from pydantic import BaseModel

from app.models.category import CategoryType


class Category(BaseModel):
    id: int
    name: str
    description: str
    type: CategoryType


class CategoryCreate(BaseModel):
    name: str
    description: str
    type: CategoryType


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: CategoryType | None = None
