from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.models import (
    BillingAccumulated,
    Invoice,
    Payment,
    PaymentMethod,
    TenantVersionHistory,
)
from app.modules.billing.paypal import create_paypal_order
from app.modules.billing.stripe import create_payment_intent
from app.modules.orders.models import Order
from app.modules.tenants.models import Tenant

RATES = {
    "lite": Decimal("0.01"),
    "full": Decimal("0.025"),
    "full_brikick": Decimal("0.02"),
}

MINIMUMS = {
    "EUR": Decimal("10.00"),
    "USD": Decimal("5.00"),
    "GBP": Decimal("8.00"),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _month_bounds(target: date) -> tuple[date, date]:
    start = target.replace(day=1)
    _, last_day = calendar.monthrange(target.year, target.month)
    end = target.replace(day=last_day)
    return start, end


def _year_month(target: date) -> str:
    return f"{target.year:04d}-{target.month:02d}"


def _period_datetime_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end, time.max, tzinfo=timezone.utc)
    return start_dt, end_dt


def _is_sqlite(db: AsyncSession) -> bool:
    bind = db.get_bind()
    return bool(bind and bind.dialect.name == "sqlite")


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def calculate_gmv(
    db: AsyncSession,
    tenant_id,
    period_start: date,
    period_end: date,
) -> Decimal:
    if _is_sqlite(db):
        orders = await _fetch_orders(db, tenant_id, period_start, period_end)
        total = Decimal("0")
        for order in orders:
            amount = _as_decimal(order.grand_total) if order.grand_total is not None else _as_decimal(order.subtotal)
            total += amount
        return total

    order_ts = func.coalesce(Order.ordered_at, Order.created_at)
    amount_expr = func.coalesce(Order.grand_total, Order.subtotal, 0)
    start_dt, end_dt = _period_datetime_bounds(period_start, period_end)
    stmt = (
        select(func.coalesce(func.sum(amount_expr), 0))
        .where(Order.tenant_id == tenant_id)
        .where(order_ts >= start_dt)
        .where(order_ts <= end_dt)
    )
    result = await db.execute(stmt)
    return _as_decimal(result.scalar_one())


async def _fetch_orders(
    db: AsyncSession,
    tenant_id,
    period_start: date,
    period_end: date,
) -> list[Order]:
    order_ts = func.coalesce(Order.ordered_at, Order.created_at)
    if _is_sqlite(db):
        stmt = select(Order).where(Order.tenant_id == tenant_id).order_by(order_ts.asc())
        result = await db.execute(stmt)
        orders = list(result.scalars().all())
        filtered: list[Order] = []
        for order in orders:
            when = _normalize_datetime(order.ordered_at or order.created_at)
            if when is None:
                continue
            when_date = when.date()
            if period_start <= when_date <= period_end:
                filtered.append(order)
        return filtered

    start_dt, end_dt = _period_datetime_bounds(period_start, period_end)
    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .where(order_ts >= start_dt)
        .where(order_ts <= end_dt)
        .order_by(order_ts.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _fetch_version_history(db: AsyncSession, tenant_id) -> list[TenantVersionHistory]:
    stmt = (
        select(TenantVersionHistory)
        .where(TenantVersionHistory.tenant_id == tenant_id)
        .order_by(TenantVersionHistory.started_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _version_for_date(
    history: list[TenantVersionHistory],
    target_day: date,
    default_version: str,
) -> str:
    for entry in history:
        started = entry.started_at.date()
        ended = entry.ended_at.date() if entry.ended_at else None
        if started <= target_day and (ended is None or target_day <= ended):
            return entry.version
    return default_version


def _version_days(
    history: list[TenantVersionHistory],
    period_start: date,
    period_end: date,
    default_version: str,
) -> dict[str, int]:
    days: dict[str, int] = {"lite": 0, "full": 0}
    current = period_start
    while current <= period_end:
        version = _version_for_date(history, current, default_version)
        days[version] = days.get(version, 0) + 1
        current += timedelta(days=1)
    return days


async def calculate_gmv_breakdown(
    db: AsyncSession,
    tenant: Tenant,
    period_start: date,
    period_end: date,
) -> dict[str, Decimal]:
    orders = await _fetch_orders(db, tenant.id, period_start, period_end)
    history = await _fetch_version_history(db, tenant.id)
    totals = {"lite": Decimal("0"), "full": Decimal("0")}
    for order in orders:
        when = (order.ordered_at or order.created_at).date()
        version = _version_for_date(history, when, tenant.current_version)
        amount = _as_decimal(order.grand_total) if order.grand_total is not None else _as_decimal(order.subtotal)
        totals[version] = totals.get(version, Decimal("0")) + amount
    return totals


async def get_billing_status(db: AsyncSession, tenant: Tenant) -> dict:
    today = _utcnow().date()
    period_start, period_end = _month_bounds(today)
    gmv = await calculate_gmv(db, tenant.id, period_start, period_end)
    has_discount = bool(tenant.has_brikick_store)
    if tenant.current_version == "lite":
        rate = RATES["lite"]
    else:
        rate = RATES["full_brikick"] if has_discount else RATES["full"]
    estimated_fee = (gmv * rate).quantize(Decimal("0.01"))
    return {
        "current_version": tenant.current_version,
        "has_brikick_discount": has_discount,
        "current_rate": rate,
        "billing_status": tenant.billing_status,
        "current_month_gmv": gmv,
        "current_month_estimated_fee": estimated_fee,
    }


async def change_tenant_version(
    db: AsyncSession,
    tenant: Tenant,
    new_version: str,
    changed_by,
    reason: str | None = None,
) -> TenantVersionHistory:
    if new_version not in {"lite", "full"}:
        raise ValueError("Invalid version")
    now = _utcnow()
    stmt = (
        select(TenantVersionHistory)
        .where(TenantVersionHistory.tenant_id == tenant.id)
        .where(TenantVersionHistory.ended_at.is_(None))
    )
    result = await db.execute(stmt)
    active = result.scalar_one_or_none()
    if active and active.version == new_version:
        return active
    if active:
        active.ended_at = now
    entry = TenantVersionHistory(
        tenant_id=tenant.id,
        version=new_version,
        started_at=now,
        changed_by=changed_by,
        change_reason=reason,
    )
    db.add(entry)
    tenant.current_version = new_version
    await db.flush()
    return entry


async def list_invoices(db: AsyncSession, tenant_id) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .where(Invoice.tenant_id == tenant_id)
        .order_by(Invoice.period_start.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_invoice(db: AsyncSession, tenant_id, invoice_id) -> Invoice | None:
    stmt = select(Invoice).where(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def generate_invoice(
    db: AsyncSession,
    tenant: Tenant,
    period_start: date,
    period_end: date,
) -> Invoice:
    year_month = _year_month(period_start)
    stmt = select(Invoice).where(Invoice.tenant_id == tenant.id, Invoice.year_month == year_month)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing

    breakdown = await calculate_gmv_breakdown(db, tenant, period_start, period_end)
    history = await _fetch_version_history(db, tenant.id)
    days = _version_days(history, period_start, period_end, tenant.current_version)

    lite_gmv = breakdown.get("lite", Decimal("0"))
    full_gmv = breakdown.get("full", Decimal("0"))
    net_gmv = lite_gmv + full_gmv

    lite_fee = (lite_gmv * RATES["lite"]).quantize(Decimal("0.01"))
    full_rate = RATES["full_brikick"] if tenant.has_brikick_store else RATES["full"]
    full_fee = (full_gmv * full_rate).quantize(Decimal("0.01"))
    subtotal = (lite_fee + full_fee).quantize(Decimal("0.01"))

    currency = tenant.billing_currency or tenant.currency or "EUR"
    minimum = MINIMUMS.get(currency, MINIMUMS["EUR"])
    accumulated = await db.get(BillingAccumulated, tenant.id)
    accumulated_amount = _as_decimal(accumulated.amount if accumulated else Decimal("0"))
    total_due = (subtotal + accumulated_amount).quantize(Decimal("0.01"))

    below_minimum = total_due < minimum
    if below_minimum:
        if not accumulated:
            accumulated = BillingAccumulated(tenant_id=tenant.id, amount=total_due, currency=currency)
            db.add(accumulated)
        else:
            accumulated.amount = total_due
            accumulated.currency = currency
            accumulated.updated_at = _utcnow()
    elif accumulated:
        accumulated.amount = Decimal("0")
        accumulated.currency = currency
        accumulated.updated_at = _utcnow()

    invoice = Invoice(
        tenant_id=tenant.id,
        period_start=period_start,
        period_end=period_end,
        year_month=year_month,
        currency=currency,
        net_gmv=net_gmv,
        lite_days=days.get("lite", 0),
        lite_gmv=lite_gmv,
        lite_fee=lite_fee,
        full_days=days.get("full", 0),
        full_gmv=full_gmv,
        full_fee=full_fee,
        brikick_discount_applied=bool(tenant.has_brikick_store and full_gmv > 0),
        subtotal=subtotal,
        accumulated_from_previous=accumulated_amount,
        total_due=total_due,
        minimum_threshold=minimum,
        below_minimum=below_minimum,
        status="DRAFT",
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def list_payment_methods(db: AsyncSession, tenant_id) -> list[PaymentMethod]:
    stmt = (
        select(PaymentMethod)
        .where(PaymentMethod.tenant_id == tenant_id)
        .order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_payment_method(
    db: AsyncSession,
    tenant_id,
    payload,
) -> PaymentMethod:
    method = PaymentMethod(tenant_id=tenant_id, **payload.model_dump())
    if payload.is_default:
        await _clear_default_payment_method(db, tenant_id)
    db.add(method)
    await db.flush()
    return method


async def _clear_default_payment_method(db: AsyncSession, tenant_id) -> None:
    stmt = select(PaymentMethod).where(
        PaymentMethod.tenant_id == tenant_id,
        PaymentMethod.is_default.is_(True),
    )
    result = await db.execute(stmt)
    for method in result.scalars().all():
        method.is_default = False


async def remove_payment_method(db: AsyncSession, method: PaymentMethod) -> None:
    await db.delete(method)


async def set_default_payment_method(db: AsyncSession, method: PaymentMethod) -> PaymentMethod:
    await _clear_default_payment_method(db, method.tenant_id)
    method.is_default = True
    await db.flush()
    return method


async def process_payment(
    db: AsyncSession,
    tenant: Tenant,
    invoice: Invoice,
    method: str,
    payment_method_id,
) -> Payment:
    if invoice.status == "PAID":
        raise ValueError("Invoice already paid")
    now = _utcnow()
    payment = Payment(
        tenant_id=tenant.id,
        invoice_id=invoice.id,
        amount=invoice.total_due,
        currency=invoice.currency,
        method=method,
        status="SUCCEEDED",
        processed_at=now,
    )
    if method == "stripe":
        intent = await create_payment_intent(
            amount=invoice.total_due,
            currency=invoice.currency,
            customer_id=tenant.stripe_customer_id,
            payment_method_id=payment_method_id,
        )
        payment.stripe_payment_intent_id = intent["id"]
    elif method == "paypal":
        order = await create_paypal_order(
            amount=invoice.total_due,
            currency=invoice.currency,
            payer_id=tenant.paypal_payer_id,
        )
        payment.paypal_order_id = order["id"]
    else:
        raise ValueError("Unsupported payment method")
    invoice.status = "PAID"
    invoice.paid_at = now
    invoice.payment_method = method
    invoice.payment_reference = payment.stripe_payment_intent_id or payment.paypal_order_id
    db.add(payment)
    await db.flush()
    return payment


def generate_invoice_pdf(invoice: Invoice) -> bytes:
    content = "\n".join(
        [
            "Brikonnect Invoice",
            f"Invoice ID: {invoice.id}",
            f"Tenant ID: {invoice.tenant_id}",
            f"Period: {invoice.period_start} - {invoice.period_end}",
            f"Total Due: {invoice.total_due} {invoice.currency}",
        ]
    )
    pdf_payload = f"%PDF-1.4\n{content}\n%%EOF"
    return pdf_payload.encode("utf-8")


async def generate_monthly_invoices(db: AsyncSession) -> list[Invoice]:
    today = _utcnow().date()
    period_start, period_end = _month_bounds(today.replace(day=1) - timedelta(days=1))
    stmt = select(Tenant).where(Tenant.billing_status == "ACTIVE")
    result = await db.execute(stmt)
    invoices = []
    for tenant in result.scalars().all():
        invoice = await generate_invoice(db, tenant, period_start, period_end)
        invoices.append(invoice)
    return invoices


async def check_overdue_invoices(db: AsyncSession) -> list[Tenant]:
    today = _utcnow().date()
    if today.day <= 5:
        return []
    stmt = select(Invoice).where(
        Invoice.status == "ISSUED",
        Invoice.due_date.is_not(None),
        Invoice.due_date < today,
    )
    result = await db.execute(stmt)
    tenants = []
    for invoice in result.scalars().all():
        tenant = await db.get(Tenant, invoice.tenant_id)
        if tenant and tenant.billing_status != "SUSPENDED":
            tenant.billing_status = "SUSPENDED"
            tenants.append(tenant)
    await db.flush()
    return tenants


async def send_invoice_reminders(db: AsyncSession) -> int:
    today = _utcnow().date()
    if today.day not in {3, 4}:
        return 0
    stmt = select(Invoice).where(
        Invoice.status == "ISSUED",
        Invoice.due_date.is_not(None),
        Invoice.due_date >= today,
    )
    result = await db.execute(stmt)
    return len(result.scalars().all())
