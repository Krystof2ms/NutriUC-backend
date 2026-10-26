from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class SessionDB:
    id: int
    token_hash: str
    jti: str
    user_id: int
    expires_at: datetime
    revoked: bool
    created_at: datetime


@dataclass(frozen=True, kw_only=True)
class SessionCreate:
    token_hash: str
    jti: UUID
    user_id: int
    expires_at: datetime
