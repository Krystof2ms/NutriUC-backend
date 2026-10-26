# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from typing import Annotated

from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from fastapi.responses import JSONResponse

from app.api.dependencies.auth import get_profile, get_profile_optional
from app.api.responses.common import MessageError, MessageResponse
from app.api.responses.definitions import COMMON_RESPONSES
from app.api.schemas.auth import AccessTokenPayload
from app.api.schemas.pagination import CursorPage
from app.api.schemas.tip import TipCreateDTO, TipDTO, TipQueryDTO, TipUpdate
from app.core.registry.category import CategoryRegistry, get_category_registry
from app.repositories.connection import get_db
from app.services.tip import service as TipService

router = APIRouter(prefix="/tips", tags=["tips"], responses=COMMON_RESPONSES)


@router.get(
    "/search",
    response_model=CursorPage[TipDTO],
    responses={
        404: {"model": MessageError, "description": "Tip not found"},
        400: {"model": MessageError, "description": "Request invalid"},
    },
)
async def findDTO(
    filter_query: Annotated[TipQueryDTO, Query()],
    conn: Connection = Depends(get_db),
    access: AccessTokenPayload | None = Depends(get_profile_optional),
):
    if filter_query.mine and access is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Session invalid")

    user_id = int(access.sub) if filter_query.mine and access else None

    tips = await TipService.getDTOWithParams(
        conn,
        name=filter_query.name,
        category=filter_query.category,
        cursor=filter_query.cursor,
        limit=filter_query.limit,
        direction=filter_query.direction,
        user_id=user_id,
    )

    return tips


@router.get(
    "/tip/{id}",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=TipDTO,
)
async def findId(id: int, conn: Connection = Depends(get_db)):
    result = await TipService.getDTO(conn, id)

    return result


@router.post(
    "/tip",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    data: TipCreateDTO,
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
    registry: CategoryRegistry = Depends(get_category_registry),
):
    category_id = registry.get(data.category)
    new = data.to_create()
    _ = await TipService.create(conn, new, category_id, int(access_token.sub))

    return JSONResponse(
        {"message": "Recipes create"}, status_code=status.HTTP_201_CREATED
    )


@router.patch(
    "/tip/{id}",
    responses={
        404: {"model": MessageError, "description": "Recipe not found"},
        400: {"model": MessageError, "description": "Request invalid"},
    },
    response_model=MessageResponse,
)
async def update(
    id: int,
    data: TipUpdate,
    conn: Connection = Depends(get_db),
    access_token: AccessTokenPayload = Depends(get_profile),
    registry: CategoryRegistry = Depends(get_category_registry),
):
    if not data.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Body is empty")

    new = data.to_update(registry.get(data.category) if data.category else None)

    await TipService.update(conn, id, int(access_token.sub), new)

    return JSONResponse({"message": "Recipe update"})


@router.delete(
    "/tip/{id}",
    responses={404: {"model": MessageError, "description": "Recipe not found"}},
    response_model=MessageResponse,
)
async def delete(
    id: int,
    access_token: AccessTokenPayload = Depends(get_profile),
    conn: Connection = Depends(get_db),
):
    await TipService.delete(conn, id, int(access_token.sub))
    return JSONResponse({"message": "Recipe delete"})
