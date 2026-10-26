from asyncpg import Connection  # pyright: ignore[reportMissingTypeStubs]

from app.api.schemas.pagination import CursorPage
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import CursorDirection, TipCreate, TipDTO, TipUpdate
from app.repositories import tip as TipRepo

from .errors import TipNotCreateError, TipNotFoundError, TipNotUpdateError

PAGE_SIZE = 12


@trace(TraceLayer.SERVICE)
async def getDTOWithParams(
    conn: Connection,
    *,
    name: str | None = None,
    category: str | None = None,
    user_id: int | None = None,
    cursor: int | None = None,
    limit: int = PAGE_SIZE,
    direction: CursorDirection = CursorDirection.NEXT,
) -> CursorPage[TipDTO]:
    result = await TipRepo.getDtoWithParams(
        conn,
        name=name,
        category=category,
        user_id=user_id,
        cursor=cursor,
        limit=limit,
        direction=direction,
    )

    if result is None:
        raise TipNotFoundError()

    return result


@trace(TraceLayer.SERVICE)
async def getDTO(conn: Connection, id: int) -> TipDTO:
    tip = await TipRepo.getDTO(conn, id)

    if tip is None:
        raise TipNotFoundError()

    return tip


@trace(TraceLayer.REPO)
async def create(
    conn: Connection,
    new: TipCreate,
    category_id: int,
    user_id: int,
) -> int:
    id = await TipRepo.create(conn, new, category_id, user_id)

    if id is None:
        raise TipNotCreateError()

    return id


@trace(TraceLayer.SERVICE)
async def update(
    conn: Connection,
    tip: int,
    user_id: int,
    data: TipUpdate,
):
    result = await TipRepo.update(conn, tip, user_id, data)

    if not result:
        raise TipNotUpdateError()


@trace(TraceLayer.SERVICE)
async def delete(
    conn: Connection,
    recipe: int,
    user_id: int,
):
    result = await TipRepo.deleteById(conn, recipe, user_id)

    if not result:
        raise TipNotFoundError()
