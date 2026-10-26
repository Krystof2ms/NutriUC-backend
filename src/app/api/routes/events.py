# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies.auth import get_profile
from app.api.schemas import AccessTokenPayload
from app.core.events.manager import event_manager

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/events")
async def events_endpoint(
    request: Request,
    access_token: AccessTokenPayload = Depends(get_profile),
):
    user_id = int(access_token.sub)
    queue = await event_manager.connect(user_id)

    async def generator():
        try:
            yield {
                "event": "connected",
                "data": "Hello",
            }

            while True:
                if await request.is_disconnected():
                    break

                event = await queue.get()

                yield event

        finally:
            await event_manager.disconnect(user_id, queue)

    return EventSourceResponse(generator())
