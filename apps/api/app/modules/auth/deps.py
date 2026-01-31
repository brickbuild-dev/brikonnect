from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token, utcnow
from app.db.session import get_db
from app.modules.auth import service as auth_service
from app.modules.tenants import service as tenant_service
from app.modules.users import service as user_service


def get_tenant_slug_from_request(request: Request) -> str | None:
    host = request.headers.get("host", "")
    host = host.split(":")[0]
    if not host or host == "localhost":
        return None
    parts = host.split(".")
    if len(parts) < 2:
        return None
    subdomain = parts[0]
    if subdomain in {"api", "www", "cdn"}:
        return None
    return subdomain


async def resolve_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    slug = get_tenant_slug_from_request(request) or settings.DEFAULT_TENANT_SLUG
    if not slug:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    tenant = await tenant_service.get_tenant_by_slug(db, slug)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_header = request.headers.get("authorization")
    user_id = None
    tenant_id = None

    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
    else:
        session_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
        if not session_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        session = await auth_service.get_session_by_token(db, session_token)
        if not session or session.expires_at <= utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        user_id = session.user_id
        tenant_id = session.tenant_id

    if not user_id or not tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)
    if isinstance(tenant_id, str):
        tenant_id = uuid.UUID(tenant_id)

    user = await user_service.get_user_by_id(db, tenant_id, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")

    if settings.ENFORCE_TENANT_HOST:
        slug = get_tenant_slug_from_request(request)
        if slug:
            tenant = await tenant_service.get_tenant_by_slug(db, slug)
            if not tenant or str(tenant.id) != str(tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch"
                )

    return user


async def get_current_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await resolve_tenant(request, db)
