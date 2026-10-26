# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from asyncpg import Connection
from fastapi import APIRouter, Depends

from app.models.category import CategoryType
from app.repositories.connection import get_db
from app.services.category import service as CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/names", response_model=list[str])
async def getNames(
    only_type: CategoryType | None = None, conn: Connection = Depends(get_db)
):
    result = await CategoryService.getAll(conn, only_type)

    names = (o.name for o in result)

    return names
