from app.services.errors import ServiceError


class RecipeNotCreateError(ServiceError):
    status_code: int = 500
    detail: str = "Recipe not created"


class RecipeNotFoundError(ServiceError):
    status_code: int = 404
    detail: str = "Recipe not found"


class RecipeNotUpdateError(ServiceError):
    status_code: int = 500
    detail: str = "Recipe not update"


class RecipeImageNotFound(ServiceError):
    status_code = 404
    detail: str = "Recipe image not found"
