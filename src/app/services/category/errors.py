from ..errors import ServiceError


class CategoryServiceError(ServiceError):
    status_code: int = 500
    detail: str = "Category error"
