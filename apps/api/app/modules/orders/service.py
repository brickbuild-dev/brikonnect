from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.orders.models import Order, OrderLine, OrderStatusEvent
from app.modules.orders.schemas import OrderCreate, OrderLineCreate, OrderUpdate


ORDER_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "NEW": {"PENDING", "CANCELLED"},
    "PENDING": {"PICKING", "CANCELLED"},
    "PICKING": {"PACKING", "CANCELLED"},
    "PACKING": {"READY", "CANCELLED"},
    "READY": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"DELIVERED", "REFUNDED"},
    "DELIVERED": {"COMPLETED", "REFUNDED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
    "REFUNDED": set(),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def list_orders(
    db: AsyncSession,
    tenant_id,
    status: str | None = None,
    q: str | None = None,
) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .options(selectinload(Order.lines))
        .order_by(Order.ordered_at.desc().nullslast())
    )
    if status:
        stmt = stmt.where(Order.status == status)
    if q:
        stmt = stmt.where(
            or_(
                Order.external_order_id.ilike(f"%{q}%"),
                Order.buyer_name.ilike(f"%{q}%"),
                Order.buyer_email.ilike(f"%{q}%"),
            )
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_order(db: AsyncSession, tenant_id, order_id) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id, Order.id == order_id)
        .options(selectinload(Order.lines))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_order(
    db: AsyncSession,
    tenant_id,
    payload: OrderCreate,
) -> Order:
    order = Order(
        tenant_id=tenant_id,
        store_id=payload.store_id,
        external_order_id=payload.external_order_id,
        status=payload.status,
        status_changed_at=_utcnow(),
        buyer_name=payload.buyer_name,
        buyer_email=payload.buyer_email,
        buyer_username=payload.buyer_username,
        ship_to=payload.ship_to,
        shipping_method=payload.shipping_method,
        subtotal=payload.subtotal,
        shipping_cost=payload.shipping_cost,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        grand_total=payload.grand_total,
        currency=payload.currency,
        ordered_at=payload.ordered_at,
        paid_at=payload.paid_at,
        shipped_at=payload.shipped_at,
    )
    db.add(order)
    await db.flush()

    await _create_lines(db, order, payload.lines, tenant_id)
    await create_status_event(db, order, None, payload.status, None, "Order created")
    await db.flush()
    return order


async def _create_lines(
    db: AsyncSession,
    order: Order,
    lines: list[OrderLineCreate],
    tenant_id,
) -> None:
    for line in lines:
        db.add(
            OrderLine(
                order_id=order.id,
                tenant_id=tenant_id,
                inventory_item_id=line.inventory_item_id,
                item_type=line.item_type,
                item_no=line.item_no,
                color_id=line.color_id,
                color_name=line.color_name,
                condition=line.condition,
                description=line.description,
                qty_ordered=line.qty_ordered,
                unit_price=line.unit_price,
                line_total=line.line_total,
            )
        )


async def update_order(db: AsyncSession, order: Order, payload: OrderUpdate) -> Order:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    await db.flush()
    return order


async def delete_order(db: AsyncSession, order: Order) -> None:
    await db.delete(order)


def validate_status_transition(current: str, next_status: str) -> None:
    allowed = ORDER_STATUS_TRANSITIONS.get(current, set())
    if next_status not in allowed:
        raise ValueError(f"Status transition not allowed: {current} -> {next_status}")


async def change_status(
    db: AsyncSession,
    order: Order,
    next_status: str,
    changed_by,
    notes: str | None = None,
) -> Order:
    validate_status_transition(order.status, next_status)
    previous = order.status
    order.status = next_status
    order.status_changed_at = _utcnow()
    if next_status == "SHIPPED":
        order.shipped_at = order.shipped_at or _utcnow()
    await create_status_event(db, order, previous, next_status, changed_by, notes)
    await db.flush()
    return order


async def create_status_event(
    db: AsyncSession,
    order: Order,
    from_status: str | None,
    to_status: str,
    changed_by,
    notes: str | None,
) -> OrderStatusEvent:
    event = OrderStatusEvent(
        order_id=order.id,
        tenant_id=order.tenant_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        notes=notes,
    )
    db.add(event)
    await db.flush()
    return event


async def list_status_events(db: AsyncSession, tenant_id, order_id) -> list[OrderStatusEvent]:
    stmt = (
        select(OrderStatusEvent)
        .where(OrderStatusEvent.tenant_id == tenant_id, OrderStatusEvent.order_id == order_id)
        .order_by(OrderStatusEvent.changed_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
