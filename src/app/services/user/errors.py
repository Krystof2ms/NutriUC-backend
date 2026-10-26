from app.services.errors import ServiceError


class UserServiceError(ServiceError):
    status_code = 500
    detail = "User error"

class UserNotUpdateError(UserServiceError):
    status_code: int = 500
    detail: str = "User not update"

class UserNotCreateError(UserServiceError):
    status_code: int = 500
    detail: str = "User not created"

class UserNotFoundError(UserServiceError):
    status_code: int = 400
    detail: str = "User Invalid credentials"

class UserUnauthorizedError(UserServiceError):
    status_code: int = 401
    detail: str = "User unauthorized"

class UserAvatarNotFoundError(UserServiceError):
    status_code = 404
    detail = "User avatar not found"

class UserAvatarNoneError(UserServiceError):
    status_code = 404
    detail = "User avatar not found"
