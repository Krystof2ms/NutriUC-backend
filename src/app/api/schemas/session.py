from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionDB(BaseModel):
    id: int
    token_hash: str
    jti: str
    user_id: int
    expires_at: datetime
    revoked: bool
    created_at: datetime


class SessionCreate(BaseModel):
    token_hash: str
    jti: UUID
    user_id: int
    expires_at: datetime
