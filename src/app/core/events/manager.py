import asyncio
from collections import defaultdict

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.events.base import Event


class EventManager:
    def __init__(self):
        self.connections: dict[int, set[asyncio.Queue]] = defaultdict(set)

    async def connect(self, user_id: int) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.connections[user_id].add(queue)
        return queue

    async def disconnect(
        self,
        user_id: int,
        queue: asyncio.Queue,
    ) -> None:
        self.connections[user_id].discard(queue)

        if not self.connections[user_id]:
            del self.connections[user_id]

    @trace(TraceLayer.EVENTS)
    async def publish(
        self,
        user_id: int,
        event: Event,
    ) -> None:
        for queue in self.connections.get(user_id, set()):
            await queue.put(event.to_dict())


event_manager = EventManager()
