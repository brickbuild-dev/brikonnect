from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import new_csrf_token, verify_password, utcnow
from app.db.session import get_db
from app.middleware.rate_limit import limiter
from app.modules.auth import service as auth_service
from app.modules.auth.deps import get_current_tenant, get_current_user, resolve_tenant
from app.modules.auth.schemas import (
    AuthMeResponse,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RevokeRequest,
    TokenResponse,
)
from app.modules.rbac import service as rbac_service
from app.modules.rbac.deps import get_current_permissions
from app.modules.users import service as user_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    tenant=Depends(resolve_tenant),
):
    user = await user_service.get_user_by_email(db, tenant.id, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    session_token = await auth_service.create_session(
        db,
        user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.SESSION_TTL_SECONDS,
        path="/",
    )

    permissions = await rbac_service.get_user_permissions(db, tenant.id, user.id)
    csrf_token = new_csrf_token()
    response.headers["X-CSRF-Token"] = csrf_token
    return LoginResponse(
        user=user,
        tenant=tenant,
        permissions=permissions,
        csrf_token=csrf_token,
    )


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if session_token:
        await auth_service.revoke_session(db, session_token)
        await db.commit()
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@router.post("/token", response_model=TokenResponse)
async def token(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    tenant=Depends(resolve_tenant),
):
    user = await user_service.get_user_by_email(db, tenant.id, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    access = auth_service.build_access_token(user)
    refresh = await auth_service.create_refresh_token(db, user)
    await db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_TTL_SECONDS,
    )


@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh = await auth_service.get_refresh_token(db, payload.refresh_token)
    if not refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if refresh.revoked_at is not None:
        await auth_service.revoke_refresh_family(db, refresh.family_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    expires_at = refresh.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    if settings.ENFORCE_TENANT_HOST:
        tenant = await resolve_tenant(request, db)
        if str(tenant.id) != str(refresh.tenant_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")

    user = await user_service.get_user_by_id(db, refresh.tenant_id, refresh.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    await auth_service.revoke_refresh_token(db, refresh)
    new_refresh = await auth_service.create_refresh_token(db, user, family_id=refresh.family_id)
    await db.commit()
    access = auth_service.build_access_token(user)
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_TTL_SECONDS,
    )


@router.post("/token/revoke")
async def revoke_token(payload: RevokeRequest, db: AsyncSession = Depends(get_db)):
    refresh = await auth_service.get_refresh_token(db, payload.refresh_token)
    if refresh and refresh.revoked_at is None:
        await auth_service.revoke_refresh_token(db, refresh)
        await db.commit()
    return {"ok": True}


@router.get("/me", response_model=AuthMeResponse)
async def me(
    user=Depends(get_current_user),
    tenant=Depends(get_current_tenant),
    permissions=Depends(get_current_permissions),
):
    return AuthMeResponse(user=user, tenant=tenant, permissions=permissions)
