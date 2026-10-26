import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import logger
from app.core.queue import avatar_queue, recipe_queue
from app.core.registry.category import CategoryRegistry
from app.core.registry.roles import RoleRegistry
from app.core.workers.avatar import AvatarWorker
from app.core.workers.recipe import RecipeWorker
from app.repositories import category as CategoryRepo
from app.repositories import role as RoleRepo
from app.repositories.connection import close, connect

avatar_worker = AvatarWorker(avatar_queue)
recipe_worker = RecipeWorker(recipe_queue)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")

    logger.info(f"Tracing Layers: {settings.TRACE_LAYERS}")

    if settings.FRONTEND_DIR:
        logger.info(f"Start frontend dir: {settings.FRONTEND_DIR}")
    else:
        logger.warning("Not set frontend dir")

    logger.info("Start resources dir")
    if not settings.RESOURCES_DIR.exists():
        logger.warning("Create resources dir")
        settings.RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    pool = await connect()
    logger.info("Database pool initialized")

    logger.info("Init Registers")
    async with pool.acquire() as conn:  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        logger.info("Init Role Registry")
        roles = await RoleRepo.getAll(conn)  # pyright: ignore[reportArgumentType]
        role_registry = RoleRegistry(roles)
        app.state.role_registry = role_registry

        logger.info("Init Category Registry")
        categories = await CategoryRepo.getAll(conn)  # pyright: ignore[reportArgumentType]
        category_registry = CategoryRegistry(categories)
        app.state.category_registry = category_registry

    logger.info("Init workers")
    worker_task_avatar = asyncio.create_task(avatar_worker.run())
    worker_task_recipe = asyncio.create_task(recipe_worker.run())

    try:
        yield
    finally:
        logger.info("Shutting down application")
        logger.info("Stop runinng workers")

        worker_task_avatar.cancel()
        try:
            await worker_task_avatar
        except asyncio.CancelledError:
            pass

        worker_task_recipe.cancel()
        try:
            await worker_task_recipe
        except asyncio.CancelledError:
            pass

        await close()
        logger.info("Database pool closed")
