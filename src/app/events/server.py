from dataclasses import dataclass, field

from .base import Event


@dataclass(frozen=True)
class ServerConnected(Event):
    event: str = field(
        default="server.connected",
        init=False,
    )

    @classmethod
    def new(cls) -> ServerConnected:
        return cls(
            data={
                "status": "connected",
            }
        )


@dataclass(frozen=True)
class ServerDisconnected(Event):
    event: str = field(
        default="server.disconnected",
        init=False,
    )

    @classmethod
    def new(cls, reason: str = "connection_closed") -> ServerDisconnected:
        return cls(
            data={
                "status": "disconnected",
                "reason": reason,
            }
        )


@dataclass(frozen=True)
class ServerError(Event):
    event: str = field(
        default="server.error",
        init=False,
    )

    @classmethod
    def new(cls, message: str) -> ServerError:
        return cls(
            data={
                "detail": message,
            }
        )


@dataclass(frozen=True)
class ServerHeartbeat(Event):
    event: str = field(
        default="server.heartbeat",
        init=False,
    )

    @classmethod
    def new(cls) -> ServerHeartbeat:
        return cls(
            data={
                "status": "alive",
            }
        )
