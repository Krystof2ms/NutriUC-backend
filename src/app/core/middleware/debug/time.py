import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response


async def time_log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.time()

    response = await call_next(request)

    duration = time.time() - start
    response.headers["X-Process-Time"] = str(duration)

    return response
