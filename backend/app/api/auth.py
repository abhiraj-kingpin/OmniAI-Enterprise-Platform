from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.rbac import require_role
from app.core.security import create_access_token, get_current_user
from app.core.users import Role, User, authenticate

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    username: str
    roles: list[Role]


@router.post("/auth/token", response_model=TokenResponse)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/auth/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]):
    return UserResponse(username=user.username, roles=user.roles)


@router.get("/auth/admin-only", response_model=UserResponse)
async def admin_only(user: Annotated[User, Depends(require_role(Role.ADMIN))]):
    """Demonstrates RBAC: only reachable with the 'admin' role's token."""
    return UserResponse(username=user.username, roles=user.roles)
