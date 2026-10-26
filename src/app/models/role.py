from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class Role:
    id: int
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, kw_only=True)
class RoleCreate:
    name: str


@dataclass(frozen=True, kw_only=True)
class RoleUpdate:
    name: str
