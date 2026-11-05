from fastapi import Request

from app.services.auth.service import AuthService
from app.services.category.service import CategoryService
from app.services.recipe.service import RecipeService
from app.services.tip.service import TipService
from app.services.token.service import TokenService
from app.services.user.service import UserService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_category_service(request: Request) -> CategoryService:
    return request.app.state.category_service


def get_recipe_service(request: Request) -> RecipeService:
    return request.app.state.recipe_service


def get_tip_service(request: Request) -> TipService:
    return request.app.state.tip_service


def get_token_service(request: Request) -> TokenService:
    return request.app.state.token_service


def get_user_service(request: Request) -> UserService:
    return request.app.state.user_service
