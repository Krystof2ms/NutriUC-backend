from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Event[T](ABC):
    event: str
    data: T

    @classmethod
    @abstractmethod
    def new(cls, *args, **kwargs) -> "Event":
            pass

    def to_dict(self) -> dict:
        return asdict(self)
