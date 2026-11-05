# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form
from fastapi.responses import JSONResponse

from app.api.dependencies.services import get_auth_service
from app.api.responses.common import MessageResponse
from app.api.responses.definitions import COMMON_RESPONSES
from app.api.responses.errors import ErrorResponse
from app.api.schemas.auth import AuthResponse, CookieRefresh, LoginForm
from app.core.cookies import (
    ACCESS_TOKEN_COOKIE,
    KEY_ACCESS_TOKEN_COOKIE,
    KEY_REFRESH_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
)
from app.services.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"], responses=COMMON_RESPONSES)


@router.post(
    "/login",
    response_model=MessageResponse[AuthResponse],
    responses={
        400: {"model": ErrorResponse, "description": "User Invalid credentials"}
    },
)
async def login(
    data: Annotated[LoginForm, Form()],
    auth_service: AuthService = Depends(get_auth_service),
):
    acess_token, refresh_token, user = await auth_service.login(
        data.email, data.password
    )
    response = JSONResponse(
        {"message": {"text": "successful login", "role": user.role}}
    )
    response.set_cookie(
        key=KEY_ACCESS_TOKEN_COOKIE, value=acess_token, **vars(ACCESS_TOKEN_COOKIE)
    )
    response.set_cookie(
        key=KEY_REFRESH_TOKEN_COOKIE, value=refresh_token, **vars(REFRESH_TOKEN_COOKIE)
    )
    return response


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    cookies: Annotated[CookieRefresh, Cookie()],
    auth_service: AuthService = Depends(get_auth_service),
):
    access_token, _ = await auth_service.refresh(cookies.refresh_token)
    response = JSONResponse({"message": "validate session"})
    response.set_cookie(
        key=KEY_ACCESS_TOKEN_COOKIE, value=access_token, **vars(REFRESH_TOKEN_COOKIE)
    )
    return response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    cookies: Annotated[CookieRefresh, Cookie()],
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.revokeSession(cookies.refresh_token)
    response = JSONResponse({"message": "revoked session"})
    response.delete_cookie(KEY_ACCESS_TOKEN_COOKIE)
    response.delete_cookie(KEY_REFRESH_TOKEN_COOKIE)
    return response
