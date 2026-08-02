"""In-memory user store, seeded with two demo accounts.

This is intentionally not a database — it's here to make the JWT/OAuth2/RBAC
flow genuinely runnable end to end. Swap `_USERS` for a real table (and
`bcrypt` stays the same) when this platform gets a persistence layer.
"""

from dataclasses import dataclass, field
from enum import StrEnum

import bcrypt


class Role(StrEnum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    username: str
    password_hash: bytes
    roles: list[Role] = field(default_factory=lambda: [Role.USER])


def _hash(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


# Demo credentials — change these before this ever touches a real deployment.
_USERS: dict[str, User] = {
    "admin": User(username="admin", password_hash=_hash("admin123"), roles=[Role.ADMIN, Role.USER]),
    "demo": User(username="demo", password_hash=_hash("demo123"), roles=[Role.USER]),
}


def get_user(username: str) -> User | None:
    return _USERS.get(username)


def authenticate(username: str, password: str) -> User | None:
    user = get_user(username)
    if user is None:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash):
        return None
    return user
