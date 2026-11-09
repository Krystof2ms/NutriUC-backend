from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.context_manager import lifespan
from app.core.config import Environments, TraceLayer, settings
from app.core.logger import logger
from app.core.middleware.debug import DebugMiddleware, list_routes, time_log_requests
from app.core.middleware.exceptions import (
    internal_server_error,
    repo_error_handler,
    service_error_handler,
    validation_error_handler,
)
from app.repositories.errorrs import RepositoryError
from app.services.errors import ServiceError

app = FastAPI(lifespan=lifespan)

if settings.FASTAPI_ENV == Environments.DEVELOPMENT:
    _ = app.middleware("http")(time_log_requests)

if TraceLayer.API in settings.TRACE_LAYERS and settings.FASTAPI_ENV == "development":
    app.add_middleware(DebugMiddleware)

app.add_exception_handler(ServiceError, service_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(RepositoryError, repo_error_handler)
app.add_exception_handler(Exception, internal_server_error)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

if settings.FASTAPI_ENV == Environments.DEVELOPMENT:
    logger.info("list routes:")
    list_routes(app.routes)

if settings.FRONTEND_DIR:
    app.frontend("/", directory=settings.FRONTEND_DIR)
