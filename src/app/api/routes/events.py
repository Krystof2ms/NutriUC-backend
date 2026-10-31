# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.dependencies.auth import get_profile
from app.api.schemas import AccessTokenPayload
from app.core.events.manager import event_manager
from app.core.logger import logger

router = APIRouter(prefix="/events", tags=["events"])


@router.websocket("/connect")
async def events_endpoint(
    websocket: WebSocket,
    access_token: AccessTokenPayload = Depends(get_profile),
):
    user_id = int(access_token.sub)
    queue = await event_manager.connect(user_id)

    await websocket.accept()

    async def send_events():
        while True:
            event = await queue.get()
            await websocket.send_json(event)

    async def receive_messages():
        while True:
            await websocket.receive_text()

    send_task = asyncio.create_task(send_events())
    receive_task = asyncio.create_task(receive_messages())

    try:
        await websocket.send_json(
            {
                "event": "server.connected",
                "data": {
                    "status": "connected",
                },
            }
        )

        _, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected for user %s", user_id)
    finally:
        send_task.cancel()
        receive_task.cancel()
        await event_manager.disconnect(user_id, queue)
