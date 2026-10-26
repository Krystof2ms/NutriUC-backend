from dataclasses import dataclass, field
from pathlib import Path

from .base import Job


@dataclass(frozen=True)
class ProcessRecipeImageData:
    user_id: int
    recipe_id: int
    source_path: Path


@dataclass(frozen=True)
class ProcessRecipeImage(Job[ProcessRecipeImageData]):
    type: str = field(default="user.image_changed", init=False)

    @classmethod
    def new(
        cls, user_id: int, recipe_id: int, source_path: Path
    ) -> "ProcessRecipeImage":
        return cls(
            data=ProcessRecipeImageData(
                user_id=user_id,
                recipe_id=recipe_id,
                source_path=source_path,
            )
        )
