from starlette.routing import Mount, Route, WebSocketRoute

from app.core.logger import logger


def list_routes(routes, prefix=""):
    for r in routes:
        if isinstance(r, WebSocketRoute):  # APIWebSocketRoute hereda de este
            logger.info(f"WS    {'':<15} {prefix}{r.path}")
        elif isinstance(r, Route):  # APIRoute también hereda de Route
            methods = ",".join(sorted(r.methods or []))
            logger.info(f"HTTP  {methods:<15} {prefix}{r.path}")
        elif isinstance(r, Mount):
            list_routes(r.routes, prefix + r.path)
        elif hasattr(r, "original_router"):  # fastapi.routing._IncludedRouter
            extra = r.include_context.prefix or ""
            list_routes(r.original_router.routes, prefix + extra)
        else:
            logger.info(f"???   {type(r)}")
