from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class JobQueue[T](ABC):
    @abstractmethod
    async def enqueue(self, job: T) -> None:
        pass

    @abstractmethod
    async def dequeue(self) -> T:
        pass

    @abstractmethod
    def task_done(self) -> None:
        pass
