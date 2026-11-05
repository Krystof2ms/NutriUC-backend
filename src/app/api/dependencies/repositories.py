from fastapi import Request

from app.repositories.interfaces.category import CategoryRepositoryInterface
from app.repositories.interfaces.recipe import RecipeRepositoryInterface
from app.repositories.interfaces.role import RoleRepositoryInterface
from app.repositories.interfaces.session import SessionRepositoryInterface
from app.repositories.interfaces.tip import TipRepositoryInterface
from app.repositories.interfaces.user import UserRepositoryInterface


def get_category_repository(request: Request) -> CategoryRepositoryInterface:
    return request.app.state.category_repository


def get_recipe_repository(request: Request) -> RecipeRepositoryInterface:
    return request.app.state.recipe_repository


def get_role_repository(request: Request) -> RoleRepositoryInterface:
    return request.app.state.role_repository


def get_session_repository(request: Request) -> SessionRepositoryInterface:
    return request.app.state.session_repository


def get_tip_repository(request: Request) -> TipRepositoryInterface:
    return request.app.state.tip_repository


def get_user_repository(request: Request) -> UserRepositoryInterface:
    return request.app.state.user_repository
