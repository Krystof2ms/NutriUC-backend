from asyncio import Queue

from app.jobs.recipe import ProcessRecipeImage

from .base import JobQueue


class RecipeJobQueue(JobQueue[ProcessRecipeImage]):
    def __init__(self) -> None:
        self._queue: Queue[ProcessRecipeImage] = Queue()

    async def enqueue(self, job: ProcessRecipeImage) -> None:
        await self._queue.put(job)

    async def dequeue(self) -> ProcessRecipeImage:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()


recipe_queue = RecipeJobQueue()
