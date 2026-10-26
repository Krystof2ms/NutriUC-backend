from asyncpg import Record

from app.models.recipe import RecipeDTO
from app.models.user import UserSummary


def parser_dto(row: Record) -> RecipeDTO:
    return RecipeDTO(
        id=row["id"],
        name=row["name"],
        origin=row["origin"],
        instructions=row["instructions"],
        ingredients=row["ingredients"],
        description=row["description"],
        created_at=row["created_at"],
        category=row["category"],
        has_image=row["has_image"],
        owner=UserSummary(
            public_id=row["owner_id"],
            name=row["owner_name"],
            has_image=row["owner_avatar"]
        ),
    )
