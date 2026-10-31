from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any


class EventBaseModel(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class Event[T = dict[str, str]](EventBaseModel, ABC):
    event: str
    data: T

    @classmethod
    @abstractmethod
    def new(cls, *args: Any, **kwargs: Any) -> Event[Any]:
        ...

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
