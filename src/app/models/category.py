from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel


class CategoryType(StrEnum):
    RECIPE = "recipe"
    TIP = "tip"
    ALL = "all"


@dataclass(frozen=True, kw_only=True)
class Category:
    id: int
    name: str
    description: str
    type: CategoryType


@dataclass(frozen=True, kw_only=True)
class CategoryCreate:
    name: str
    description: str
    type: CategoryType


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: CategoryType | None = None
