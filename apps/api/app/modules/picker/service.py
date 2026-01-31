from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.inventory.models import InventoryItemLocation
from app.modules.locations.models import Location
from app.modules.orders.models import Order, OrderLine
from app.modules.picker.models import PickEvent, PickSession, PickSessionOrder
from app.modules.picker.schemas import PickEventCreate, PickSessionCreate, PickSessionUpdate, PickRouteItem


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def list_sessions(db: AsyncSession, tenant_id, status: str | None = None) -> list[PickSession]:
    stmt = select(PickSession).where(PickSession.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(PickSession.status == status)
    result = await db.execute(stmt.order_by(PickSession.created_at.desc()))
    return list(result.scalars().all())


async def get_session(db: AsyncSession, tenant_id, session_id) -> PickSession | None:
    stmt = (
        select(PickSession)
        .where(PickSession.tenant_id == tenant_id, PickSession.id == session_id)
        .options(selectinload(PickSession.orders))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession, tenant_id, user_id, payload: PickSessionCreate
) -> PickSession:
    orders_result = await db.execute(
        select(Order).where(Order.tenant_id == tenant_id, Order.id.in_(payload.order_ids))
    )
    orders = list(orders_result.scalars().all())
    if len(orders) != len(set(payload.order_ids)):
        raise ValueError("One or more orders not found for tenant.")

    lines_result = await db.execute(
        select(OrderLine).where(
            OrderLine.tenant_id == tenant_id, OrderLine.order_id.in_(payload.order_ids)
        )
    )
    lines = list(lines_result.scalars().all())

    session = PickSession(
        tenant_id=tenant_id,
        created_by=user_id,
        status="DRAFT",
        total_orders=len(orders),
        total_items=sum(line.qty_ordered for line in lines),
        notes=payload.notes,
    )
    db.add(session)
    await db.flush()

    for idx, order in enumerate(orders):
        db.add(
            PickSessionOrder(
                pick_session_id=session.id,
                order_id=order.id,
                sort_order=idx,
            )
        )
    await db.flush()
    return session


async def update_session(
    db: AsyncSession, session: PickSession, payload: PickSessionUpdate
) -> PickSession:
    if payload.status:
        session.status = payload.status
        if payload.status == "ACTIVE" and session.started_at is None:
            session.started_at = _utcnow()
        if payload.status == "COMPLETED" and session.completed_at is None:
            session.completed_at = _utcnow()
    if payload.notes is not None:
        session.notes = payload.notes
    await db.flush()
    return session


async def record_event(
    db: AsyncSession,
    session: PickSession,
    user_id,
    payload: PickEventCreate,
) -> PickEvent:
    line_result = await db.execute(
        select(OrderLine).where(OrderLine.id == payload.order_line_id)
    )
    line = line_result.scalar_one_or_none()
    if not line:
        raise ValueError("Order line not found.")
    if line.tenant_id != session.tenant_id:
        raise ValueError("Order line does not belong to this tenant.")

    if payload.event_type.upper() == "PICKED":
        line.qty_picked = min(line.qty_ordered, line.qty_picked + payload.qty)
    elif payload.event_type.upper() == "MISSING":
        line.qty_missing = min(line.qty_ordered, line.qty_missing + payload.qty)

    if line.qty_picked >= line.qty_ordered:
        line.status = "PICKED"
    elif line.qty_picked > 0:
        line.status = "PARTIAL"
    elif line.qty_missing > 0:
        line.status = "MISSING"

    if payload.event_type.upper() == "PICKED":
        session.picked_items = session.picked_items + payload.qty

    event = PickEvent(
        pick_session_id=session.id,
        order_line_id=payload.order_line_id,
        user_id=user_id,
        event_type=payload.event_type.upper(),
        qty=payload.qty,
        location_code=payload.location_code,
        notes=payload.notes,
    )
    db.add(event)
    await db.flush()
    return event


async def list_events(db: AsyncSession, tenant_id, session_id) -> list[PickEvent]:
    stmt = (
        select(PickEvent)
        .join(PickSession, PickEvent.pick_session_id == PickSession.id)
        .where(PickSession.tenant_id == tenant_id, PickEvent.pick_session_id == session_id)
        .order_by(PickEvent.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def build_route(
    db: AsyncSession, tenant_id, session_id
) -> list[PickRouteItem]:
    stmt = (
        select(
            OrderLine.order_id,
            OrderLine.id,
            OrderLine.item_no,
            OrderLine.qty_ordered,
            func.min(Location.code),
        )
        .join(PickSessionOrder, PickSessionOrder.order_id == OrderLine.order_id)
        .join(PickSession, PickSession.id == PickSessionOrder.pick_session_id)
        .outerjoin(
            InventoryItemLocation,
            InventoryItemLocation.inventory_item_id == OrderLine.inventory_item_id,
        )
        .outerjoin(Location, Location.id == InventoryItemLocation.location_id)
        .where(PickSession.id == session_id, PickSession.tenant_id == tenant_id)
        .group_by(OrderLine.order_id, OrderLine.id, OrderLine.item_no, OrderLine.qty_ordered)
        .order_by(func.min(Location.code).asc().nullslast(), OrderLine.item_no)
    )
    result = await db.execute(stmt)
    items: list[PickRouteItem] = []
    for order_id, line_id, item_no, qty_ordered, location_code in result.all():
        items.append(
            PickRouteItem(
                order_id=order_id,
                order_line_id=line_id,
                item_no=item_no,
                qty_ordered=qty_ordered,
                location_code=location_code,
            )
        )
    return items
