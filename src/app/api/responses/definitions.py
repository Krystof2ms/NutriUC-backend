from typing import Any

from app.api.responses.common import MessageError
from app.api.responses.errors import ValidationErrorResponse

COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {  # pyright: ignore[reportExplicitAny]
    422: {
        "model": ValidationErrorResponse,
        "description": "Validation error",
    },
    500: {
        "model": MessageError,
        "description": "Internal server error",
    },
}
