from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.repositories.errorrs import RepositoryError
from app.services.errors import ServiceError


async def service_error_handler(
    _: Request,
    exc: Exception,
):
    if not isinstance(exc, ServiceError):
        raise exc

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def repo_error_handler(
    _: Request,
    exc: Exception,
):
    if not isinstance(exc, RepositoryError):
        raise exc

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_error_handler(
    _: Request,
    exc: Exception,
):
    if not isinstance(exc, RequestValidationError):
        raise exc

    errors = []

    for error in exc.errors():  # pyright: ignore[reportAny]
        loc = error["loc"]  # pyright: ignore[reportAny]

        field = loc[-1] if loc else None

        errors.append(  # pyright: ignore[reportUnknownMemberType]
            {
                "field": field,
                "code": error["type"],
                "message": "Invalid value",
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "There are invalid fields",
            "errors": errors,
        },
    )
