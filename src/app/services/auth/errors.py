from app.services.errors import ServiceError


class AuthServiceError(ServiceError):
    status_code: int = 500
    detail: str = "Auth Service error"


class UserInvalidError(AuthServiceError):
    status_code: int = 400
    detail: str = "User Invalid"


class UserInvalidCredentialsError(AuthServiceError):
    status_code: int = 400
    detail: str = "User Invalid credentials"


class UserNotPasswordError(AuthServiceError):
    status_code: int = 404
    detail: str = "User uses external authentication"


class TokenInvalidError(AuthServiceError):
    status_code: int = 400
    detail: str = "Refresh token revoked or expired"


class TokenNotRevokedError(AuthServiceError):
    status_code: int = 500
    detail: str = "Refresh token not revoked"
