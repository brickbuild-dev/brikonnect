from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.security import verify_password, hash_password, new_session_token, expires_in, sign_token
from app.crud.tenants import get_tenant_by_slug, create_tenant
from app.crud.users import get_user_by_email, create_user
from app.models.session import Session
from app.schemas.auth import LoginRequest, LoginResponse, TokenResponse

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # Minimal multi-tenant strategy:
    # - In production: derive tenant from subdomain/host header.
    # - In this scaffold: default tenant "demo".
    tenant = await get_tenant_by_slug(db, "demo")
    if not tenant:
        tenant = await create_tenant(db, slug="demo", name="Demo Tenant")

    user = await get_user_by_email(db, tenant.id, payload.username)
    if not user:
        # For scaffold usability, auto-provision first user
        user = await create_user(db, tenant.id, payload.username, hash_password(payload.password), is_superuser=True)

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = new_session_token()
    sess = Session(
        tenant_id=tenant.id,
        user_id=user.id,
        session_token=token,
        expires_at=expires_in(settings.SESSION_TTL_SECONDS),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
    )
    db.add(sess)
    await db.commit()

    # Session cookie: allow_credentials=True on CORS and proxy for same-origin.
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # set True behind TLS
        samesite="lax",
        max_age=settings.SESSION_TTL_SECONDS,
        path="/",
    )
    return LoginResponse(user_id=user.id, tenant_id=tenant.id, email=user.email)

@router.post("/token", response_model=TokenResponse)
async def token(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Optional bearer token for service-to-service usage.
    tenant = await get_tenant_by_slug(db, "demo")
    if not tenant:
        raise HTTPException(status_code=400, detail="Tenant not initialized")

    user = await get_user_by_email(db, tenant.id, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access = sign_token({"sub": user.id, "tenant_id": tenant.id})
    return TokenResponse(access_token=access)

@router.post("/logout")
async def logout(response: Response):
    # Soft logout: client deletes cookie. In production, also delete server session token.
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return {"ok": True}
