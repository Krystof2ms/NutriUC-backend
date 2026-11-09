# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status

from app.api.dependencies.services import (
    get_auth_service,
    get_token_service,
    get_user_service,
)
from app.api.schemas.auth import AccessTokenPayload, CookiesAuth
from app.core.cookies import ACCESS_TOKEN_COOKIE, KEY_ACCESS_TOKEN_COOKIE
from app.services.auth.errors import AuthServiceError
from app.services.auth.service import AuthService
from app.services.token.errors import InvalidAccessTokenError
from app.services.token.service import TokenService
from app.services.user.service import UserService


async def get_access_payload(
    cookies: Annotated[CookiesAuth, Cookie()],
    token_service: TokenService = Depends(get_token_service),
) -> AccessTokenPayload:
    if cookies.access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token not found",
        )

    try:
        return await token_service.verifyAccessToken(cookies.access_token)
    except InvalidAccessTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )


async def get_profile(
    response: Response,
    cookies: Annotated[CookiesAuth, Cookie()],
    token_service: TokenService = Depends(get_token_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenPayload:

    if cookies.access_token is not None:
        try:
            return await token_service.verifyAccessToken(cookies.access_token)
        except InvalidAccessTokenError:
            pass

    if cookies.refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    try:
        access_token, payload = await auth_service.refresh(cookies.refresh_token)

        response.set_cookie(
            key=KEY_ACCESS_TOKEN_COOKIE,
            value=access_token,
            **vars(ACCESS_TOKEN_COOKIE),
        )

        return payload

    except AuthServiceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid",
        )


async def get_profile_ws(
    payload: AccessTokenPayload = Depends(get_access_payload),
) -> AccessTokenPayload:
    return payload


async def get_access_payload_optional(
    cookies: Annotated[CookiesAuth, Cookie()],
    token_service: TokenService = Depends(get_token_service),
) -> AccessTokenPayload | None:

    if cookies.access_token is None:
        return None

    try:
        return await token_service.verifyAccessToken(cookies.access_token)
    except InvalidAccessTokenError:
        return None


async def get_profile_optional(
    payload: AccessTokenPayload | None = Depends(get_access_payload_optional),
) -> AccessTokenPayload | None:
    return payload


async def require_admin(
    access_token: AccessTokenPayload = Depends(get_profile),
    user_service: UserService = Depends(get_user_service),
) -> AccessTokenPayload:

    user = await user_service.getUserDB(user_id=int(access_token.sub))

    if user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return access_token
