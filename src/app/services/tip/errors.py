from app.services.errors import ServiceError


class TipNotCreateError(ServiceError):
    status_code: int = 500
    detail: str = "Tip not created"


class TipNotFoundError(ServiceError):
    status_code: int = 404
    detail: str = "Tip not found"


class TipNotUpdateError(ServiceError):
    status_code: int = 500
    detail: str = "Tip not update"
