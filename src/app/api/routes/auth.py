# pyright: reportCallInDefaultInitializer=false

from typing import Annotated

from asyncpg.connection import Connection  # pyright: ignore[reportMissingTypeStubs]
from fastapi import APIRouter, Cookie, Depends, Form
from fastapi.responses import JSONResponse

from app.api.responses.common import MessageResponse
from app.api.responses.definitions import COMMON_RESPONSES
from app.api.responses.errors import ErrorResponse
from app.api.schemas.auth import CookieRefresh, LoginForm
from app.core.cookies import (
    ACCESS_TOKEN_COOKIE,
    KEY_ACCESS_TOKEN_COOKIE,
    KEY_REFRESH_TOKEN_COOKIE,
    REFRESH_TOKEN_COOKIE,
)
from app.repositories.connection import get_db
from app.services.auth import service as AuthService

router = APIRouter(prefix="/auth", tags=["auth"], responses=COMMON_RESPONSES)


@router.post(
    "/login",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "User Invalid credentials"}
    },
)
async def login(
    data: Annotated[LoginForm, Form()],
    conn: Connection = Depends(get_db),  # noqa: B008
):
    acess_token, refresh_token, _ = await AuthService.login(
        conn, data.email, data.password
    )

    response = JSONResponse({"message": "login sussed"})
    response.set_cookie(
        key=KEY_ACCESS_TOKEN_COOKIE,
        value=acess_token,
        **vars(ACCESS_TOKEN_COOKIE),  # pyright: ignore[reportAny]
    )
    response.set_cookie(
        key=KEY_REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        **vars(REFRESH_TOKEN_COOKIE),  # pyright: ignore[reportAny]
    )

    return response


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    cookies: Annotated[CookieRefresh, Cookie()],
    conn: Connection = Depends(get_db),  # noqa: B008
):
    access_token, _ = await AuthService.refresh(conn, cookies.refresh_token)

    response = JSONResponse({"message": "validate session"})
    response.set_cookie(
        key=KEY_ACCESS_TOKEN_COOKIE,
        value=access_token,
        **vars(REFRESH_TOKEN_COOKIE),  # pyright: ignore[reportAny]
    )

    return response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    cookies: Annotated[CookieRefresh, Cookie()],
    conn: Connection = Depends(get_db),  # noqa: B008
):
    await AuthService.revokeSession(conn, cookies.refresh_token)

    response = JSONResponse({"message": "revoked session"})
    response.delete_cookie(KEY_ACCESS_TOKEN_COOKIE)
    response.delete_cookie(KEY_REFRESH_TOKEN_COOKIE)
    return response
