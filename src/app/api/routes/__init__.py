from fastapi import APIRouter

from . import auth, categories, events, recipes, tips, user


def init_routers(router: APIRouter):
    router.include_router(auth.router)
    router.include_router(recipes.router)
    router.include_router(tips.router)
    router.include_router(user.router)
    router.include_router(categories.router)
    router.include_router(events.router)
