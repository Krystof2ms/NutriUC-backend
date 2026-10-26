from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


class ValidationErrorItem(BaseModel):
    field: str | None
    code: str
    message: str


class ValidationErrorResponse(BaseModel):
    code: str
    message: str
    errors: list[ValidationErrorItem]
