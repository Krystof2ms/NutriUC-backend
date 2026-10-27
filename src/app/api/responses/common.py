from pydantic import BaseModel


class MessageResponse[T = str](BaseModel):
    message: T


class MessageError(BaseModel):
    detail: str
