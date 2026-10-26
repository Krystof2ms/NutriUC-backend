class ServiceError(Exception):
    status_code: int = 500
    detail: str = "Service error"
