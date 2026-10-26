from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class MessageError(BaseModel):
    detail: str
