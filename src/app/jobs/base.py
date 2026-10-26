from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Job[T](ABC):
    type: str
    data: T

    @classmethod
    @abstractmethod
    def new(cls, *args, **kwargs) -> "Job":
        pass
