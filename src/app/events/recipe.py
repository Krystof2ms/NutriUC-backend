from dataclasses import dataclass, field

from .base import Event


@dataclass(frozen=True)
class RecipeImageChanged(Event):
    event: str = field(
        default="recipe.image_changed",
        init=False,
    )

    @classmethod
    def new(cls) -> "RecipeImageChanged":
        return cls(
            data={
                "message": "image accept",
            }
        )


@dataclass(frozen=True)
class RecipeImageRejected(Event):
    event: str = field(
        default="recipe.image_rejected",
        init=False,
    )

    @classmethod
    def new(cls, message: str) -> "RecipeImageRejected":
        return cls(
            data={
                "detail": message,
            }
        )
