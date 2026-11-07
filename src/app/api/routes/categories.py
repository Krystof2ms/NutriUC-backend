# pyright: reportCallInDefaultInitializer=false
# ruff: noqa: B008

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_category_service
from app.models.category import CategoryType
from app.services.category.service import CategoryService

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/names", response_model=list[str])
async def get_names(
    only_type: CategoryType | None = None,
    category_service: CategoryService = Depends(get_category_service),
):
    result = await category_service.getAll(only_type)
    names = (o.name for o in result)
    return names
