# pyright: reportCallInDefaultInitializer=false

from typing import Annotated

from asyncpg import Connection  # pyright: ignore[reportMissingTypeStubs]
from fastapi import Cookie, Depends, HTTPException, Response, status

from app.api.schemas.auth import AccessTokenPayload, CookiesAuth
from app.core.cookies import ACCESS_TOKEN_COOKIE, KEY_ACCESS_TOKEN_COOKIE
from app.repositories.connection import get_db
from app.services.auth import service as AuthService
from app.services.auth.errors import AuthServiceError
from app.services.token import service as TokenService
from app.services.token.errors import InvalidAccessTokenError
from app.services.user import service as UserService


async def get_cookies_auth(cookies: Annotated[CookiesAuth, Cookie()]):
    if cookies.refresh_token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    access_payload = None

    if cookies.access_token is not None:  # pyright: ignore[reportUnnecessaryComparison]
        try:
            access_payload = await TokenService.verifyAccessToken(cookies.access_token)
        except InvalidAccessTokenError:
            access_payload = None

    return cookies.refresh_token, access_payload


async def get_profile(
    response: Response,
    tokens: tuple[str, AccessTokenPayload | None] = Depends(get_cookies_auth),
    db: Connection = Depends(get_db),  # noqa: B008
) -> AccessTokenPayload:
    payload = tokens[1]

    if payload is None:
        try:
            access_token, payload = await AuthService.refresh(db, tokens[0])
            response.set_cookie(
                key=KEY_ACCESS_TOKEN_COOKIE,
                value=access_token,
                **vars(ACCESS_TOKEN_COOKIE),  # pyright: ignore[reportAny]
            )

            return payload
        except AuthServiceError:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalidate"
            )

    return payload


async def get_cookies_auth_optional(cookies: Annotated[CookiesAuth, Cookie()]):
    if cookies.refresh_token is None:
        return None

    access_payload = None

    if cookies.access_token is not None:  # pyright: ignore[reportUnnecessaryComparison]
        try:
            access_payload = await TokenService.verifyAccessToken(cookies.access_token)
        except InvalidAccessTokenError:
            access_payload = None

    return access_payload


async def get_profile_optional(
    access: AccessTokenPayload | None = Depends(get_cookies_auth_optional),  # noqa: B008
) -> AccessTokenPayload | None:
    return access


async def require_admin(
    access_token: AccessTokenPayload = Depends(get_profile),  # noqa: B008
    db: Connection = Depends(get_db),  # noqa: B008
) -> AccessTokenPayload:
    user = await UserService.getUserDB(conn=db, user_id=int(access_token.sub))

    if user.role.lower() != "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return access_token
