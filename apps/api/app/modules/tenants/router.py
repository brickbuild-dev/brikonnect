from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.deps import get_current_tenant
from app.modules.rbac.deps import require_permissions
from app.modules.tenants.schemas import TenantOut, TenantUpdate
from app.modules.tenants.service import update_tenant

router = APIRouter()


@router.get("/me", response_model=TenantOut)
async def me(tenant=Depends(get_current_tenant)):
    return tenant


@router.patch("/me", response_model=TenantOut)
async def update_me(
    payload: TenantUpdate,
    tenant=Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permissions(["settings:write"])),
):
    tenant = await update_tenant(db, tenant, payload)
    await db.commit()
    return tenant
