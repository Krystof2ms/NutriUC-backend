import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database.postgres.database import PostgresDatabase
from app.core.logger import logger
from app.core.queue import avatar_queue, recipe_queue
from app.core.registry.category import CategoryRegistry
from app.core.registry.roles import RoleRegistry
from app.core.workers.avatar import AvatarWorker
from app.core.workers.recipe import RecipeWorker
from app.repositories.category import CategoryRepository
from app.repositories.recipe.funcs import RecipeRepository
from app.repositories.role import RoleRepository
from app.repositories.session import SessionRepository
from app.repositories.tip.funcs import TipRepository
from app.repositories.user import UserRepository
from app.services.auth.service import AuthService
from app.services.category.service import CategoryService
from app.services.recipe.service import RecipeService
from app.services.tip.service import TipService
from app.services.token.service import TokenService
from app.services.user.service import UserService


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    logger.info("Tracing Layers: %s", settings.TRACE_LAYERS)

    if settings.FRONTEND_DIR:
        logger.info("Start frontend dir: %s", settings.FRONTEND_DIR)
    else:
        logger.warning("Not set frontend dir")

    logger.info("Start resources dir")
    if not settings.RESOURCES_DIR.exists():
        logger.warning("Create resources dir")
        settings.RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    pool = await PostgresDatabase.create_pool()
    database = PostgresDatabase(pool)
    app.state.pool = pool
    app.state.database = database

    app.state.user_repository = UserRepository(database)
    app.state.session_repository = SessionRepository(database)
    app.state.role_repository = RoleRepository(database)
    app.state.category_repository = CategoryRepository(database)
    app.state.recipe_repository = RecipeRepository(database)
    app.state.tip_repository = TipRepository(database)

    app.state.token_service = TokenService()
    app.state.user_service = UserService(app.state.user_repository)
    app.state.auth_service = AuthService(
        app.state.user_repository, app.state.session_repository, app.state.token_service
    )
    app.state.category_service = CategoryService(app.state.category_repository)
    app.state.recipe_service = RecipeService(app.state.recipe_repository)
    app.state.tip_service = TipService(app.state.tip_repository)

    avatar_worker = AvatarWorker(avatar_queue, app.state.user_repository)
    recipe_worker = RecipeWorker(recipe_queue, app.state.recipe_repository)

    try:
        logger.info("Database connection established")
        logger.info("Database pool initialized")

        logger.info("Init Registers")
        roles = await app.state.role_repository.getAll()
        app.state.role_registry = RoleRegistry(roles)
        categories = await app.state.category_repository.getAll()
        app.state.category_registry = CategoryRegistry(categories)

        logger.info("Init workers")
        worker_task_avatar = asyncio.create_task(avatar_worker.run())
        worker_task_recipe = asyncio.create_task(recipe_worker.run())
        try:
            yield
        finally:
            logger.info("Shutting down application")
            logger.info("Stop running workers")
            for task in (worker_task_avatar, worker_task_recipe):
                task.cancel()
            for task in (worker_task_avatar, worker_task_recipe):
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    finally:
        await pool.close()
        logger.info("Database pool closed")
