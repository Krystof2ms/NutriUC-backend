from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AccessTokenPayload(BaseModel):
    sub: str
    exp: datetime


class RefreshTokenPayload(BaseModel):
    exp: datetime
    sub: str
    jti: str


class CookieRefresh(BaseModel):
    refresh_token: str


class CookiesAuth(BaseModel):
    refresh_token: str | None = None
    access_token: str | None = None


class LoginForm(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=20)
