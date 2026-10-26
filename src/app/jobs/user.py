from dataclasses import dataclass, field
from pathlib import Path

from .base import Job


@dataclass(frozen=True)
class Crop:
    x: float
    y: float
    size: float


@dataclass(frozen=True)
class ProcessUserAvatarData:
    user_id: int
    source_path: Path
    crop: Crop


@dataclass(frozen=True)
class ProcessUserAvatar(Job[ProcessUserAvatarData]):
    type: str = field(default="user.image_changed", init=False)

    @classmethod
    def new(cls, user_id: int, source_path: Path, crop: Crop) -> "ProcessUserAvatar":
        return cls(
            data=ProcessUserAvatarData(
                user_id=user_id,
                source_path=source_path,
                crop=crop,
            )
        )
