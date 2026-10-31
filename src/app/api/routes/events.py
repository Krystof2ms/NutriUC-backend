# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

import json

from fastapi import APIRouter, Depends, Request
from sse_starlette.event import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies.auth import get_profile
from app.api.schemas import AccessTokenPayload
from app.core.events.manager import event_manager
from app.core.logger import logger

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
            yield ServerSentEvent(
                event="connected",
                data="Hello",
            )

            while True:
                if await request.is_disconnected():
                    break

                event = await queue.get()

                logger.info("SSE: queue event received: %r", event)
                logger.info("Event type: %s", type(event))
                logger.info("Event content: %r", event)

                if isinstance(event, dict):
                    logger.info("Event name: %r", event.get("event"))
                    logger.info("Event data: %r", event.get("data"))

                yield ServerSentEvent(
                    event=event["event"],
                    data=json.dumps(event["data"]),
                )

        finally:
            await event_manager.disconnect(user_id, queue)

    return EventSourceResponse(generator())
