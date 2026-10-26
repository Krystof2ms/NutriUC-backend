from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.models.user import UserSummary


@dataclass(frozen=True, kw_only=True)
class Instruction:
    step: int
    instruction: str


@dataclass(frozen=True, kw_only=True)
class Ingredient:
    name: str
    quantity: str


@dataclass(frozen=True, kw_only=True)
class RecipeBase:
    name: str
    origin: str
    instructions: list[Instruction]
    ingredients: list[Ingredient]
    description: str


@dataclass(frozen=True, kw_only=True)
class RecipeCreate(RecipeBase):
    image_key: str | None = None


class RecipeUpdate(BaseModel):
    name: str | None = None
    origin: str | None = None
    instructions: list[Instruction] | None = None
    ingredients: list[Ingredient] | None = None
    description: str | None = None
    category_id: int | None = None


@dataclass(frozen=True, kw_only=True)
class RecipeDB(RecipeBase):
    category_id: int
    user_id: int
    image_key: str | None
    id: int
    updated_at: datetime
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class RecipeDTO(RecipeBase):
    id: int
    category: str
    owner: UserSummary
    created_at: datetime
    has_image: bool

    @classmethod
    def from_base(
        cls,
        base: RecipeBase,
        *,
        id: int,
        category: str,
        owner: UserSummary,
        created_at: datetime,
    ) -> "RecipeDTO":
        return cls(
            id=id,
            name=base.name,
            origin=base.origin,
            instructions=base.instructions,
            ingredients=base.ingredients,
            description=base.description,
            category=category,
            owner=owner,
            created_at=created_at,
        )
