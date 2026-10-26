from app.services.errors import ServiceError


class TokenServiceError(ServiceError):
    status_code: int = 500
    detail: str = "Auth Service error"


class InvalidAccessTokenError(TokenServiceError):
    status_code: int = 401
    detail: str = "Invalid access token"


class InvalidRefreshTokenError(TokenServiceError):
    status_code: int = 401
    detail: str = "Invalid refresh token"
