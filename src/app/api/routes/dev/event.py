# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies.auth import require_admin
from app.api.responses.common import MessageResponse
from app.api.schemas import AccessTokenPayload, Event
from app.core.events.manager import event_manager

router = APIRouter(prefix="/event")


@router.get("/connect")
async def dev_event_stream(
    access_token: AccessTokenPayload = Depends(require_admin),
):
    user_id = int(access_token.sub)
    queue = await event_manager.connect(user_id)

    async def generator():
        try:
            yield {"event": "connected", "data": "dev event stream ready"}

            while True:
                event = await queue.get()
                yield event
        finally:
            await event_manager.disconnect(user_id, queue)

    return EventSourceResponse(generator())


@router.post("/send/{id}", response_model=MessageResponse)
async def dev_event_send(id: int, event: Event):
    await event_manager.publish(id, event)

    return {"message": "Event sent successfully"}
