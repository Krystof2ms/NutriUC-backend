import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from app.core.config import TraceLayer, settings
from app.core.logger import logger

P = ParamSpec("P")
T = TypeVar("T")

SKIP_PARAMS = {"conn", "request", "response"}


def trace(layer: TraceLayer, skip_params: set[str] | None = None):
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        signature = inspect.signature(func)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            if layer not in settings.TRACE_LAYERS:
                return await func(*args, **kwargs)

            bound = signature.bind(*args, **kwargs)

            skip = SKIP_PARAMS.union(skip_params) if skip_params else SKIP_PARAMS

            params = {
                name: value
                for name, value in bound.arguments.items()  # pyright: ignore[reportAny]
                if name not in skip
            }

            logger.info(
                "%s | %s | %s",
                layer.value,
                func.__name__,
                params,
            )

            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                logger.exception(
                    "%s | %s | %s | %s",
                    layer.value,
                    func.__name__,
                    type(exc).__name__,
                    params,
                )
                raise

        return wrapper

    return decorator
