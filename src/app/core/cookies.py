from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class CookieConfig:
    path: str = "/"
    domain: str | None = None
    secure: bool = True
    httponly: bool = True
    samesite: str = "lax"
    max_age: int | None = None
    expires: int | None = None
    partitioned: bool = False

KEY_ACCESS_TOKEN_COOKIE = "access_token"
ACCESS_TOKEN_COOKIE = CookieConfig(
    path="/",
    httponly=True,
    secure=settings.FASTAPI_ENV == "production",
    samesite="lax",
)

KEY_REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_COOKIE = CookieConfig(
    path="/",
    httponly=True,
    secure=settings.FASTAPI_ENV == "production",
    samesite="strict",
)
