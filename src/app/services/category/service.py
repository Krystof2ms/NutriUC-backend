from app.core.config import TraceLayer
from app.core.decorator import trace
from app.models.category import Category, CategoryType
from app.repositories.interfaces.category import CategoryRepositoryInterface


class CategoryService:
    def __init__(self, category_repo: CategoryRepositoryInterface):
        self.category_repo = category_repo

    @trace(TraceLayer.SERVICE)
    async def getAll(self, only_type: CategoryType | None = None) -> list[Category]:
        categories = await self.category_repo.getAll(only_type=only_type)
        return categories
