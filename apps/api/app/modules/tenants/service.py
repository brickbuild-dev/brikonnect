from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas import TenantCreate, TenantUpdate


async def get_tenant_by_id(db: AsyncSession, tenant_id) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    return result.scalar_one_or_none()


async def list_tenants(db: AsyncSession) -> list[Tenant]:
    result = await db.execute(select(Tenant).order_by(Tenant.created_at))
    return list(result.scalars().all())


async def create_tenant(db: AsyncSession, payload: TenantCreate) -> Tenant:
    tenant = Tenant(
        slug=payload.slug,
        name=payload.name,
        plan=payload.plan,
        currency=payload.currency,
        current_version=payload.current_version,
        has_brikick_store=payload.has_brikick_store,
        billing_currency=payload.billing_currency,
        billing_email=payload.billing_email,
        billing_status=payload.billing_status,
        stripe_customer_id=payload.stripe_customer_id,
        paypal_payer_id=payload.paypal_payer_id,
    )
    db.add(tenant)
    await db.flush()
    return tenant


async def update_tenant(db: AsyncSession, tenant: Tenant, payload: TenantUpdate) -> Tenant:
    if payload.name is not None:
        tenant.name = payload.name
    if payload.plan is not None:
        tenant.plan = payload.plan
    if payload.currency is not None:
        tenant.currency = payload.currency
    if payload.current_version is not None:
        tenant.current_version = payload.current_version
    if payload.has_brikick_store is not None:
        tenant.has_brikick_store = payload.has_brikick_store
    if payload.billing_currency is not None:
        tenant.billing_currency = payload.billing_currency
    if payload.billing_email is not None:
        tenant.billing_email = payload.billing_email
    if payload.billing_status is not None:
        tenant.billing_status = payload.billing_status
    if payload.stripe_customer_id is not None:
        tenant.stripe_customer_id = payload.stripe_customer_id
    if payload.paypal_payer_id is not None:
        tenant.paypal_payer_id = payload.paypal_payer_id
    await db.flush()
    return tenant
