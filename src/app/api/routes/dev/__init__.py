from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_admin
from app.core.config import settings
from app.core.logger import logger

from .event import router as event_router

if settings.FASTAPI_ENV != "development":
    logger.critical(
        "Attempt to initialize dev APIs outside DEVELOPMENT environment: %s",
        settings.FASTAPI_ENV,
    )

dev_router = APIRouter(prefix="/dev", tags=["dev"], dependencies=[Depends(require_admin)])
dev_router.include_router(event_router)