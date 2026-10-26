from typing import Generic

from pydantic.main import BaseModel
from pydantic.types import T


class CursorPage(BaseModel, Generic[T]):  # noqa: UP046
    data: list[T]
    next_cursor: int | None
    previous_cursor: int | None
