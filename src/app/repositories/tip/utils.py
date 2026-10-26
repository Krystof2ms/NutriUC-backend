from asyncpg import Record

from app.models.tip import TipDTO
from app.models.user import UserSummary


def parser_dto(row: Record) -> TipDTO:
    return TipDTO(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        created_at=row["created_at"],
        category=row["category"],
        owner=UserSummary(
            public_id=row["owner_id"],
            name=row["owner_name"],
            has_image=row["owner_avatar"]
        ),
    )
