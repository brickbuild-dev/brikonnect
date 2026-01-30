from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant

async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Tenant | None:
    q = select(Tenant).where(Tenant.slug == slug)
    return (await db.execute(q)).scalars().first()

async def create_tenant(db: AsyncSession, slug: str, name: str) -> Tenant:
    tenant = Tenant(slug=slug, name=name)
    db.add(tenant)
    await db.flush()
    return tenant
