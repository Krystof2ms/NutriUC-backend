from datetime import datetime

from pydantic import BaseModel


class Role(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime


class RoleCreate(BaseModel):
    name: str


class RoleUpdate(BaseModel):
    name: str
