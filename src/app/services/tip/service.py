from app.api.schemas.pagination import CursorPage
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models import CursorDirection, TipCreate, TipDTO, TipUpdate
from app.repositories.interfaces.tip import TipRepositoryInterface

from .errors import TipNotCreateError, TipNotFoundError, TipNotUpdateError

PAGE_SIZE = 12


class TipService:
    def __init__(self, tip_repo: TipRepositoryInterface):
        self.tip_repo = tip_repo

    @trace(TraceLayer.SERVICE)
    async def getDTOWithParams(
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        user_id: int | None = None,
        cursor: int | None = None,
        limit: int = PAGE_SIZE,
        direction: CursorDirection = CursorDirection.NEXT,
    ) -> CursorPage[TipDTO]:
        result = await self.tip_repo.getDtoWithParams(
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
    async def getDTO(self, id: int) -> TipDTO:
        tip = await self.tip_repo.getDTO(id)
        if tip is None:
            raise TipNotFoundError()
        return tip

    @trace(TraceLayer.REPO)
    async def create(self, new: TipCreate, category_id: int, user_id: int) -> int:
        id = await self.tip_repo.create(new, category_id, user_id)
        if id is None:
            raise TipNotCreateError()
        return id

    @trace(TraceLayer.SERVICE)
    async def update(self, tip: int, user_id: int, data: TipUpdate):
        result = await self.tip_repo.update(tip, user_id, data)
        if not result:
            raise TipNotUpdateError()

    @trace(TraceLayer.SERVICE)
    async def delete(self, recipe: int, user_id: int):
        result = await self.tip_repo.deleteById(recipe, user_id)
        if not result:
            raise TipNotFoundError()
