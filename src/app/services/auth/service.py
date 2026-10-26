from datetime import UTC, datetime
from hashlib import sha256

from asyncpg import Connection  # pyright: ignore[reportMissingTypeStubs]
from pwdlib import PasswordHash

from app.api.schemas.auth import AccessTokenPayload
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.session import SessionCreate
from app.models.user import UserDB, UserStatus
from app.repositories import session as SessionRepo
from app.repositories import user as UserRepo
from app.services.token import service as TokenService
from app.services.token.errors import TokenServiceError

from .errors import (
    TokenInvalidError,
    TokenNotRevokedError,
    UserInvalidCredentialsError,
    UserInvalidError,
    UserNotPasswordError,
)

password_hash = PasswordHash.recommended()


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


@trace(TraceLayer.SERVICE)
async def login(conn: Connection, email: str, password: str) -> tuple[str, str, UserDB]:
    """
    Login for user.

    Returns:
        tuple[str, str, UserDB]:
            - access_token: The encoded access JWT.
            - refresh_token: The encoded refresh JWT.
            - user: User data
    """
    user = await UserRepo.getByEmail(conn, email)

    if user is None:
        raise UserInvalidError()

    if user.status != UserStatus.ACTIVE:
        raise UserInvalidError()

    if user.password_hash is None:
        raise UserNotPasswordError()

    valid = password_hash.verify(password, user.password_hash)

    if not valid:
        raise UserInvalidCredentialsError()

    access_token, _ = await TokenService.generateAccessToken(user.id)
    refresh_token, jti, expire = await TokenService.generateRefreshToken(user.id)
    _ = await SessionRepo.create(
        conn,
        SessionCreate(
            token_hash=hash_token(refresh_token),
            jti=jti,
            user_id=user.id,
            expires_at=expire,
        ),
    )

    return access_token, refresh_token, user


@trace(TraceLayer.SERVICE)
async def refresh(
    conn: Connection, refresh_token: str
) -> tuple[str, AccessTokenPayload]:
    """
    Login for user.

    Returns:
        tuple[str, AccessTokenPayload]:
            - access_token: The encoded access JWT.
            - access_token_payload: The access payload JWT.
    """

    try:
        payload = await TokenService.verifyRefreshToken(refresh_token)
    except TokenServiceError:
        raise TokenInvalidError()

    stored = await SessionRepo.getByToken(conn, payload.jti)

    if not stored or stored.expires_at < datetime.now(UTC) or stored.revoked:
        raise TokenInvalidError()

    user = await UserRepo.getById(conn, int(payload.sub))

    if not user or user.status != UserStatus.ACTIVE:
        raise UserInvalidError()

    access_token, expire = await TokenService.generateAccessToken(user.id)

    return access_token, AccessTokenPayload(sub=str(user.id), exp=expire)


async def revokeSession(conn: Connection, refresh_token: str):
    try:
        payload = await TokenService.verifyRefreshToken(refresh_token)
    except TokenServiceError:
        raise TokenInvalidError()

    result = await SessionRepo.revokedByJti(conn, payload.jti)

    if not result:
        raise TokenNotRevokedError()
