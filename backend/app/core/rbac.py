"""Role-based access control on top of the JWT dependency in security.py."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.core.users import Role, User


def require_role(*roles: Role) -> Callable[..., User]:
    """Build a dependency that only allows users holding at least one of
    the given roles. Usage: `Depends(require_role(Role.ADMIN))`.
    """

    async def _check(user: Annotated[User, Depends(get_current_user)]) -> User:
        if not any(r in user.roles for r in roles):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires one of roles: {', '.join(roles)}",
            )
        return user

    return _check
