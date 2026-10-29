import asyncio
from collections import defaultdict

from app.core.config import TraceLayer
from app.core.decorator import trace
from app.events.base import Event


class EventManager:
    def __init__(self):
        self.connections: dict[int, set[asyncio.Queue]] = defaultdict(set)
        self.global_connections: set[asyncio.Queue] = set()

    async def connect(self, user_id: int) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.connections[user_id].add(queue)
        return queue

    async def connect_global(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.global_connections.add(queue)
        return queue

    async def disconnect_global(self, queue: asyncio.Queue) -> None:
        self.global_connections.discard(queue)

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
        payload = event.to_dict()

        print(f"Publishing event for user {user_id}: {payload}")

        for queue in self.connections.get(user_id, set()):
            await queue.put(payload)

        for queue in self.global_connections:
            await queue.put(
                {
                    **payload,
                    "data": {
                        "user_id": user_id,
                        "payload": payload["data"],
                    },
                }
            )


event_manager = EventManager()
