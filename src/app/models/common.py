from enum import StrEnum


class CursorDirection(StrEnum):
    NEXT = "next"
    PREVIOUS = "previous"

    @property
    def sql_order(self) -> str:
        return "ASC" if self is CursorDirection.NEXT else "DESC"

    @property
    def sql_operator(self) -> str:
        return ">" if self is CursorDirection.NEXT else "<"

    @property
    def opposite(self) -> CursorDirection:
        return (
            CursorDirection.PREVIOUS
            if self is CursorDirection.NEXT
            else CursorDirection.NEXT
        )
