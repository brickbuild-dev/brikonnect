from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import get_current_user
from app.crud.tenants import get_tenant_by_slug, create_tenant
from app.schemas.tenant import TenantCreate, TenantOut

router = APIRouter()

@router.post("/", response_model=TenantOut)
async def create(payload: TenantCreate, db: AsyncSession = Depends(get_db)):
    t = await create_tenant(db, slug=payload.slug, name=payload.name)
    await db.commit()
    return TenantOut(id=t.id, slug=t.slug, name=t.name)

@router.get("/me", response_model=TenantOut)
async def me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = await get_tenant_by_slug(db, "demo")
    # For scaffold: always demo
    return TenantOut(id=t.id, slug=t.slug, name=t.name)
