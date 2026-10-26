from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pydantic_core import ValidationError

from app.api.schemas.auth import AccessTokenPayload, RefreshTokenPayload
from app.core.config import TraceLayer, settings
from app.core.decorator import trace

from .errors import InvalidAccessTokenError, InvalidRefreshTokenError

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=30)
REFRESH_TOKEN_EXPIRE_MINUTES = timedelta(days=7)


@trace(TraceLayer.SERVICE)
async def generateAccessToken(
    user_id: int, expires_delta: timedelta = ACCESS_TOKEN_EXPIRE_MINUTES
) -> tuple[str, datetime]:
    """
    Generate a access token for the given user.

    Returns:
        tuple[str, str, datetime]:
            - token: The encoded access JWT.
            - datetime: expire time
    """
    expire = datetime.now(UTC) + expires_delta
    payload = AccessTokenPayload.model_construct(sub=str(user_id), exp=expire)

    return jwt.encode(  # pyright: ignore[reportUnknownMemberType]
        payload.model_dump(), settings.JWT_SECRET, algorithm=ALGORITHM
    ), expire


@trace(TraceLayer.SERVICE)
async def generateRefreshToken(
    user_id: int, expires_delta: timedelta = REFRESH_TOKEN_EXPIRE_MINUTES
) -> tuple[str, str, datetime]:
    """
    Generate a refresh token for the given user.

    Returns:
        tuple[str, str, datetime]:
            - token: The encoded refresh JWT.
            - jti: The unique identifier of the token.
            - datetime: expire time
    """
    jti = str(uuid4())
    expire = datetime.now(UTC) + expires_delta
    payload = RefreshTokenPayload.model_construct(sub=str(user_id), jti=jti, exp=expire)

    return (
        jwt.encode(  # pyright: ignore[reportUnknownMemberType]
            payload.model_dump(), settings.JWT_SECRET, algorithm=ALGORITHM
        ),
        jti,
        expire,
    )


@trace(TraceLayer.SERVICE)
async def verifyAccessToken(token: str) -> AccessTokenPayload:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])  # pyright: ignore[reportUnknownMemberType]
        decode = AccessTokenPayload(**payload)  # pyright: ignore[reportAny]
        return decode
    except ValidationError, jwt.InvalidTokenError, jwt.exceptions.ExpiredSignatureError:
        raise InvalidAccessTokenError()


@trace(TraceLayer.SERVICE)
async def verifyRefreshToken(token: str) -> RefreshTokenPayload:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])  # pyright: ignore[reportUnknownMemberType]
        decode = RefreshTokenPayload(**payload)  # pyright: ignore[reportAny]
        return decode
    except ValidationError, jwt.InvalidTokenError, jwt.exceptions.ExpiredSignatureError:
        raise InvalidRefreshTokenError()
