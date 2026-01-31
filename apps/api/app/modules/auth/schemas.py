from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.modules.tenants.schemas import TenantOut
from app.modules.users.schemas import UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginResponse(BaseModel):
    user: UserOut
    tenant: TenantOut
    permissions: list[str]
    csrf_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class RevokeRequest(BaseModel):
    refresh_token: str


class AuthMeResponse(BaseModel):
    user: UserOut
    tenant: TenantOut
    permissions: list[str]
