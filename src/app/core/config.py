from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logger import logger


class TraceLayer(StrEnum):
    API = "api"
    SERVICE = "service"
    REPO = "repo"
    DB = "db"
    WORKER = "worker"
    EVENTS = "events"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_parse_none_str="None",
    )

    API_V1_STR: str = "/api/v1"
    FASTAPI_ENV: Literal["development", "production"] = "development"
    DATABASE_URL: PostgresDsn | None = None
    CORS_ORIGINS: list[str] | None = None
    TRACE_LAYERS: set[TraceLayer] = set()
    JWT_SECRET: str | None = None
    RESOURCES_DIR: Path = Path("./resources.temp")
    FRONTEND_DIR: Path | None = Path("./dist/frontend")

    @field_validator("DATABASE_URL")
    @classmethod
    def check_db_name(cls, v: PostgresDsn | None) -> PostgresDsn:
        if v is None:
            raise ValueError("DATABASE_URL must be provided")

        if not v.path or len(v.path) <= 1:
            raise ValueError("database must be provided")
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def check_jwt_secret(cls, v: str | None) -> str:
        if v is None:
            raise ValueError("JWT_SECRET must be provided")

        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def check_cors_origins(
        cls,
        v: list[str] | None,
        info: ValidationInfo,
    ):
        env = info.data.get("FASTAPI_ENV")

        if v is None:
            if env == "production":
                raise ValueError("CORS_ORIGINS must be provided")

            logger.warning("CORS_ORIGINS not configured, using '*'")
            return ["*"]

        if "*" in v and env == "production":
            raise ValueError("CORS_ORIGINS '*' is not allowed in production")

        return v


settings = Settings()
