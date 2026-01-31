from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.v1.endpoints.auth import login as core_login
from app.api.v1.endpoints.tenants import create as core_create_tenant
from app.api.deps import get_current_user
from app.schemas.auth import LoginRequest

router = APIRouter()

# --- Compatibility layer for a Vue UI that calls /api/v1/users/* and /api/v1/tenant/* ---

@router.post("/users/login/")
async def users_login(payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # Delegates to the core login flow (cookie session).
    return await core_login(payload=payload, request=request, response=response, db=db)

@router.get("/users/user/")
async def users_user(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }

@router.post("/tenant/tenant/")
async def tenant_bootstrap(payload: dict, db: AsyncSession = Depends(get_db)):
    # Minimal shim: accepts {slug,name} and creates tenant.
    class _T:  # lightweight adapter to reuse pydantic schema indirectly
        slug = payload.get("slug", "demo")
        name = payload.get("name", "Demo Tenant")
    return await core_create_tenant(payload=_T, db=db)  # type: ignore[arg-type]

@router.get("/tenant/tenant/detail/")
async def tenant_detail(user=Depends(get_current_user)):
    # Extend later with real tenant settings (currency, address, integrations flags).
    return {
        "slug": "demo",
        "name": "Demo Tenant",
        "currency": "EUR",
        "country": "PT",
        "features": {
            "inventory": True,
            "orders": True,
            "picker": True,
            "billing": True,
            "shipping": False,
            "payments": False,
        },
    }

@router.post("/tenant/tenant/detail/")
async def tenant_detail_update(payload: dict, user=Depends(get_current_user)):
    # Stub: accept and echo; persist when you add a tenant_settings table.
    return {"ok": True, "updated": payload}
