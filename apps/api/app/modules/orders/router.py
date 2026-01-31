from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.audit.deps import get_audit_context
from app.modules.audit.service import create_audit_log, serialize_model
from app.modules.orders.schemas import (
    OrderCreate,
    OrderLineOut,
    OrderOut,
    OrderStatusEventOut,
    OrderStatusUpdate,
    OrderUpdate,
)
from app.modules.orders.service import (
    change_status,
    create_order,
    delete_order,
    get_order,
    list_orders,
    list_status_events,
    update_order,
)
from app.modules.rbac.deps import require_permissions

router = APIRouter()


@router.get("/", response_model=list[OrderOut])
async def list_all(
    status: str | None = None,
    q: str | None = None,
    current_user=Depends(require_permissions(["orders:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_orders(db, current_user.tenant_id, status, q)


@router.post("/", response_model=OrderOut, status_code=201)
async def create(
    payload: OrderCreate,
    current_user=Depends(require_permissions(["orders:write"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    order = await create_order(db, current_user.tenant_id, payload)
    await create_audit_log(
        db,
        ctx,
        action="order.create",
        entity_type="order",
        entity_id=order.id,
        before_state=None,
        after_state=serialize_model(order, exclude={"lines", "status_events"}),
    )
    await db.commit()
    order = await get_order(db, current_user.tenant_id, order.id)
    return order


@router.get("/{order_id}", response_model=OrderOut)
async def get(
    order_id: UUID,
    current_user=Depends(require_permissions(["orders:read"])),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order(db, current_user.tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderOut)
async def update(
    order_id: UUID,
    payload: OrderUpdate,
    current_user=Depends(require_permissions(["orders:write"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order(db, current_user.tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    before_state = serialize_model(order, exclude={"lines", "status_events"})
    order = await update_order(db, order, payload)
    await create_audit_log(
        db,
        ctx,
        action="order.update",
        entity_type="order",
        entity_id=order.id,
        before_state=before_state,
        after_state=serialize_model(order, exclude={"lines", "status_events"}),
    )
    await db.commit()
    order = await get_order(db, current_user.tenant_id, order_id)
    return order


@router.delete("/{order_id}", status_code=204)
async def delete(
    order_id: UUID,
    current_user=Depends(require_permissions(["orders:cancel"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order(db, current_user.tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    before_state = serialize_model(order, exclude={"lines", "status_events"})
    await delete_order(db, order)
    await create_audit_log(
        db,
        ctx,
        action="order.delete",
        entity_type="order",
        entity_id=order.id,
        before_state=before_state,
        after_state=None,
    )
    await db.commit()
    return Response(status_code=204)


@router.post("/{order_id}/status", response_model=OrderOut)
async def update_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    current_user=Depends(require_permissions(["orders:status_update"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order(db, current_user.tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    before_state = serialize_model(order, exclude={"lines", "status_events"})
    try:
        order = await change_status(db, order, payload.status, current_user.id, payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await create_audit_log(
        db,
        ctx,
        action="order.status_update",
        entity_type="order",
        entity_id=order.id,
        before_state=before_state,
        after_state=serialize_model(order, exclude={"lines", "status_events"}),
    )
    await db.commit()
    order = await get_order(db, current_user.tenant_id, order_id)
    return order


@router.get("/{order_id}/lines", response_model=list[OrderLineOut])
async def list_lines(
    order_id: UUID,
    current_user=Depends(require_permissions(["orders:read"])),
    db: AsyncSession = Depends(get_db),
):
    order = await get_order(db, current_user.tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.lines


@router.get("/{order_id}/history", response_model=list[OrderStatusEventOut])
async def history(
    order_id: UUID,
    current_user=Depends(require_permissions(["orders:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_status_events(db, current_user.tenant_id, order_id)
