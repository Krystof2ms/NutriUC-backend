from fastapi.requests import HTTPConnection
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logger import logger


class DebugMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        match scope["type"]:
            case "http":
                await self._handle_http(scope, receive, send)
            case "websocket":
                await self._handle_websocket(scope, receive, send)
            case _:  # lifespan
                await self.app(scope, receive, send)

    @staticmethod
    def _format(scope: Scope, method: str, body: str = "") -> str:
        conn = HTTPConnection(scope)
        return (
            f"\n========== REQUEST ==========\n"
            f"{method} {conn.url}\n"
            f"Headers: {dict(conn.headers)}\n"
            f"Cookies: {conn.cookies}\n"
            f"Body: {body}\n"
            f"=============================\n"
        )

    # ---------- HTTP ----------
    async def _handle_http(self, scope: Scope, receive: Receive, send: Send):
        messages: list[Message] = []
        body = b""
        while True:
            message = await receive()
            messages.append(message)
            if message["type"] != "http.request":  # disconnect
                break
            body += message.get("body", b"")
            if not message.get("more_body", False):
                break

        logger.info(self._format(scope, scope["method"], body.decode("utf-8", errors="replace")))

        async def replay_receive() -> Message:
            if messages:
                return messages.pop(0)
            return await receive()

        await self.app(scope, replay_receive, send)

    # ---------- WebSocket ----------
    async def _handle_websocket(self, scope: Scope, receive: Receive, send: Send):
        logger.info(self._format(scope, "WS"))

        async def debug_receive() -> Message:
            message = await receive()
            if message["type"] == "websocket.receive":
                payload = message.get("text") or repr(message.get("bytes"))
                logger.info(self._format(scope, "WS MESSAGE", payload))
            elif message["type"] == "websocket.disconnect":
                logger.info("WS DISCONNECT: %s", message)
            return message

        async def debug_send(message: Message) -> None:
            if message["type"] == "websocket.close":
                logger.error("WS CLOSE: %s", message)
            await send(message)

        await self.app(scope, debug_receive, debug_send)
