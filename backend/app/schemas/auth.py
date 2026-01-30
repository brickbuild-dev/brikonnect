from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    username: EmailStr
    password: str = Field(min_length=1, max_length=200)

class LoginResponse(BaseModel):
    ok: bool = True
    user_id: int
    tenant_id: int
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
