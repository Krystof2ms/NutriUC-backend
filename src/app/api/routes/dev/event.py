# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

import asyncio

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.api.dependencies.auth import require_admin
from app.api.responses.common import MessageResponse
from app.api.schemas import AccessTokenPayload, Event
from app.core.events.manager import event_manager

router = APIRouter(prefix="/events")


@router.websocket("/connect/me")
async def dev_event_stream(
    websocket: WebSocket,
    access_token: AccessTokenPayload = Depends(require_admin),
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
            {"event": "connected", "data": "dev event stream ready"}
        )

        _done_tasks, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except WebSocketDisconnect:
        pass
    finally:
        send_task.cancel()
        receive_task.cancel()
        await event_manager.disconnect(user_id, queue)


@router.websocket("/connect/all")
async def dev_all_event_stream(
    websocket: WebSocket,
    event_type: str | None = None,
    admin_token: AccessTokenPayload = Depends(require_admin),
):
    queue = await event_manager.connect_global()

    await websocket.accept()

    async def send_events():
        while True:
            event = await queue.get()

            if event_type and event.get("event") != event_type:
                continue

            await websocket.send_json(event)

    async def receive_messages():
        while True:
            await websocket.receive_text()

    send_task = asyncio.create_task(send_events())
    receive_task = asyncio.create_task(receive_messages())

    try:
        await websocket.send_json(
            {
                "event": "connected",
                "data": "dev event stream ready",
            }
        )

        _done_tasks, pending = await asyncio.wait(
            [send_task, receive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        send_task.cancel()
        receive_task.cancel()
        await event_manager.disconnect_global(queue)


@router.post("/send/{id}", response_model=MessageResponse)
async def dev_event_send(id: int, event: Event):
    await event_manager.publish(id, event.to_event())

    return {"message": "Event sent successfully"}
