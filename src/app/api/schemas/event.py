from typing import Any

from pydantic import BaseModel

from app.events.base import EventBaseModel


class Event(BaseModel, EventBaseModel):
    event: str
    data: Any

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
