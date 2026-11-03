from typing import Any

from pydantic import BaseModel

from app.events.base import EventBaseModel
from app.events.server import ServerMessageDev


class Event(BaseModel, EventBaseModel):
    event: str
    data: Any

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def to_event(self):
        return ServerMessageDev(event=self.event, data=self.data)
