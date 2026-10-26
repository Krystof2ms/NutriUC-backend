from collections.abc import Callable

from fastapi import Request

from app.models.category import Category


class CategoryRegistry:
    def __init__(self, categories: list[Category]):
        self._categories_dict: dict[str, int] = {
            category.name: category.id for category in categories
        }

    def set(self, name: str, role_id: int) -> None:
        self._categories_dict[name] = role_id

    def get(self, name: str) -> int:
        return self._categories_dict[name]

    def categories_names(
        self, transform: Callable[[str], str] | None = None
    ) -> list[str]:
        names = self._categories_dict.keys()
        list_names = list(names)

        if transform is not None:
            return list(map(transform, list_names))

        return list_names


def get_category_registry(request: Request) -> CategoryRegistry:
    return request.app.state.category_registry  # pyright: ignore[reportAny]
