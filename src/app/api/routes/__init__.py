from fastapi import APIRouter

from app.core.config import settings

from . import auth, categories, events, recipes, tips, user
from .dev import dev_router


def init_routers(router: APIRouter):
    router.include_router(auth.router)
    router.include_router(recipes.router)
    router.include_router(tips.router)
    router.include_router(user.router)
    router.include_router(categories.router)
    router.include_router(events.router)

    if settings.FASTAPI_ENV == "development":
        router.include_router(dev_router)
