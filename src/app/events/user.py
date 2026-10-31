from dataclasses import dataclass, field

from .base import Event


@dataclass(frozen=True)
class UserAvatarChanged(Event):
    event: str = field(
        default="user.image_changed",
        init=False,
    )

    @classmethod
    def new(cls) -> UserAvatarChanged:
        return cls(
            data={
                "message": "avatar accept",
            }
        )


@dataclass(frozen=True)
class UserAvatarRejected(Event):
    event: str = field(
        default="user.image_rejected",
        init=False,
    )

    @classmethod
    def new(cls, message: str) -> "UserAvatarRejected":
        return cls(
            data={
                "detail": message,
            }
        )
