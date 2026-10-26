import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.logger import logger


async def time_log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.time()

    response = await call_next(request)

    duration = time.time() - start
    response.headers["X-Process-Time"] = str(duration)

    return response

async def debug_request(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    body = await request.body()

    request_info = (
        f"\n========== REQUEST ==========\n"
        f"{request.method} {request.url}\n"
        f"Headers: {dict(request.headers)}\n"
        f"Cookies: {request.cookies}\n"
        f"Body: {body.decode('utf-8', errors='replace')}\n"
        f"=============================\n"
    )

    logger.info(request_info)

    response = await call_next(request)
    return response
