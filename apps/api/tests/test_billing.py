import calendar
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.security import hash_password
from app.modules.billing.models import BillingAccumulated, TenantVersionHistory
from app.modules.billing.service import calculate_gmv, check_overdue_invoices, generate_invoice
from app.modules.orders.schemas import OrderCreate, OrderLineCreate
from app.modules.orders.service import create_order
from app.modules.rbac import service as rbac_service
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, set_user_roles


async def seed_owner(db_session, slug: str, email: str, password: str):
    tenant = await create_tenant(db_session, TenantCreate(slug=slug, name=slug.title()))
    await rbac_service.seed_system_roles(db_session, tenant.id)
    roles = await rbac_service.list_roles(db_session, tenant.id)
    owner_role = next(role for role in roles if role.name == "owner")
    user = await create_user(
        db_session,
        tenant.id,
        UserCreate(email=email, password=password),
        hash_password(password),
    )
    await set_user_roles(db_session, tenant.id, user.id, [owner_role.id])
    await db_session.commit()
    return tenant, user


def _make_order_payload(total: str, ordered_at: datetime) -> OrderCreate:
    return OrderCreate(
        external_order_id=f"ORDER-{ordered_at.timestamp()}",
        status="NEW",
        buyer_name="Billing Buyer",
        ordered_at=ordered_at,
        grand_total=Decimal(total),
        currency="EUR",
        lines=[
            OrderLineCreate(
                item_type="PART",
                item_no="3001",
                condition="NEW",
                qty_ordered=1,
                unit_price=Decimal("0.10"),
                line_total=Decimal("0.10"),
            )
        ],
    )


@pytest.mark.asyncio
async def test_gmv_calculation(db_session):
    tenant, _ = await seed_owner(db_session, "billing-gmv", "owner@gmv.local", "billing123")

    now = datetime.now(timezone.utc)
    await create_order(db_session, tenant.id, _make_order_payload("10.00", now - timedelta(days=1)))
    await create_order(db_session, tenant.id, _make_order_payload("5.50", now - timedelta(days=2)))
    await db_session.commit()

    period_start = date(now.year, now.month, 1)
    _, last_day = calendar.monthrange(now.year, now.month)
    period_end = date(now.year, now.month, last_day)

    gmv = await calculate_gmv(db_session, tenant.id, period_start, period_end)
    assert gmv == Decimal("15.50")


@pytest.mark.asyncio
async def test_prorata_version_change(db_session):
    tenant, user = await seed_owner(db_session, "billing-prorata", "owner@prorata.local", "billing123")

    period_start = date(2026, 1, 1)
    period_end = date(2026, 1, 31)
    db_session.add(
        TenantVersionHistory(
            tenant_id=tenant.id,
            version="lite",
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ended_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            changed_by=user.id,
            change_reason="downgrade",
        )
    )
    db_session.add(
        TenantVersionHistory(
            tenant_id=tenant.id,
            version="full",
            started_at=datetime(2026, 1, 16, tzinfo=timezone.utc),
            changed_by=user.id,
            change_reason="upgrade",
        )
    )
    await create_order(
        db_session,
        tenant.id,
        _make_order_payload("20.00", datetime(2026, 1, 10, tzinfo=timezone.utc)),
    )
    await create_order(
        db_session,
        tenant.id,
        _make_order_payload("40.00", datetime(2026, 1, 20, tzinfo=timezone.utc)),
    )
    await db_session.commit()

    invoice = await generate_invoice(db_session, tenant, period_start, period_end)
    assert invoice.lite_gmv == Decimal("20.00")
    assert invoice.full_gmv == Decimal("40.00")
    assert invoice.lite_days == 15
    assert invoice.full_days == 16


@pytest.mark.asyncio
async def test_minimum_threshold_accumulation(db_session):
    tenant, _ = await seed_owner(db_session, "billing-minimum", "owner@minimum.local", "billing123")

    period_start = date(2026, 2, 1)
    period_end = date(2026, 2, 28)
    await create_order(
        db_session,
        tenant.id,
        _make_order_payload("1.00", datetime(2026, 2, 5, tzinfo=timezone.utc)),
    )
    await db_session.commit()

    invoice = await generate_invoice(db_session, tenant, period_start, period_end)
    assert invoice.below_minimum is True
    accumulated = await db_session.get(BillingAccumulated, tenant.id)
    assert accumulated is not None
    assert accumulated.amount == invoice.total_due


@pytest.mark.asyncio
async def test_invoice_generation(db_session):
    tenant, _ = await seed_owner(db_session, "billing-invoice", "owner@invoice.local", "billing123")

    period_start = date(2026, 3, 1)
    period_end = date(2026, 3, 31)
    await create_order(
        db_session,
        tenant.id,
        _make_order_payload("30.00", datetime(2026, 3, 10, tzinfo=timezone.utc)),
    )
    await db_session.commit()

    invoice = await generate_invoice(db_session, tenant, period_start, period_end)
    await db_session.commit()
    assert invoice.year_month == "2026-03"

    invoice_again = await generate_invoice(db_session, tenant, period_start, period_end)
    assert invoice.id == invoice_again.id


@pytest.mark.asyncio
async def test_overdue_suspension(db_session):
    today = datetime.now(timezone.utc).date()
    if today.day <= 5:
        pytest.skip("Overdue suspension runs after day 5")

    tenant, _ = await seed_owner(db_session, "billing-overdue", "owner@overdue.local", "billing123")
    period_start = today.replace(day=1)
    period_end = today
    invoice = await generate_invoice(db_session, tenant, period_start, period_end)
    invoice.status = "ISSUED"
    invoice.due_date = today - timedelta(days=2)
    await db_session.commit()

    tenants = await check_overdue_invoices(db_session)
    await db_session.commit()
    assert tenants
    assert tenant.billing_status == "SUSPENDED"
