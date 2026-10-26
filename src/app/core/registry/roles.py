from fastapi import Request

from app.models.role import Role


class RoleRegistry:
    def __init__(self, roles: list[Role]):
        self._roles: dict[str, int] = {role.name: role.id for role in roles}

    def set(self, name: str, role_id: int) -> None:
        self._roles[name] = role_id

    def get(self, name: str) -> int:
        return self._roles[name]

def get_role_registry(request: Request) -> RoleRegistry:
    return request.app.state.role_registry  # pyright: ignore[reportAny]
