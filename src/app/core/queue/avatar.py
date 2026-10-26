from asyncio import Queue

from app.jobs.user import ProcessUserAvatar

from .base import JobQueue


class AvatarJobQueue(JobQueue[ProcessUserAvatar]):
    def __init__(self) -> None:
        self._queue: Queue[ProcessUserAvatar] = Queue()

    async def enqueue(self, job: ProcessUserAvatar) -> None:
        await self._queue.put(job)

    async def dequeue(self) -> ProcessUserAvatar:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()


avatar_queue = AvatarJobQueue()
