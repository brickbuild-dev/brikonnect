from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.audit.deps import get_audit_context
from app.modules.audit.service import create_audit_log, serialize_model
from app.modules.picker.schemas import (
    PickEventCreate,
    PickEventOut,
    PickRouteItem,
    PickSessionCreate,
    PickSessionOut,
    PickSessionUpdate,
)
from app.modules.picker.service import (
    build_route,
    create_session,
    get_session,
    list_events,
    list_sessions,
    record_event,
    update_session,
)
from app.modules.rbac.deps import require_permissions

router = APIRouter()


def _session_out(session) -> PickSessionOut:
    order_ids = [link.order_id for link in session.orders] if session.orders else []
    return PickSessionOut(
        id=session.id,
        tenant_id=session.tenant_id,
        created_by=session.created_by,
        status=session.status,
        total_orders=session.total_orders,
        total_items=session.total_items,
        picked_items=session.picked_items,
        started_at=session.started_at,
        completed_at=session.completed_at,
        notes=session.notes,
        created_at=session.created_at,
        order_ids=order_ids,
    )


@router.get("/sessions", response_model=list[PickSessionOut])
async def list_all(
    status: str | None = None,
    current_user=Depends(require_permissions(["picker:read"])),
    db: AsyncSession = Depends(get_db),
):
    sessions = await list_sessions(db, current_user.tenant_id, status)
    return [_session_out(session) for session in sessions]


@router.post("/sessions", response_model=PickSessionOut, status_code=201)
async def create(
    payload: PickSessionCreate,
    current_user=Depends(require_permissions(["picker:create_session"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await create_session(db, current_user.tenant_id, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await create_audit_log(
        db,
        ctx,
        action="picker.session_create",
        entity_type="pick_session",
        entity_id=session.id,
        before_state=None,
        after_state=serialize_model(session, exclude={"orders", "events"}),
    )
    await db.commit()
    session = await get_session(db, current_user.tenant_id, session.id)
    return _session_out(session)


@router.get("/sessions/{session_id}", response_model=PickSessionOut)
async def get(
    session_id: UUID,
    current_user=Depends(require_permissions(["picker:read"])),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, current_user.tenant_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Pick session not found")
    return _session_out(session)


@router.patch("/sessions/{session_id}", response_model=PickSessionOut)
async def update(
    session_id: UUID,
    payload: PickSessionUpdate,
    current_user=Depends(require_permissions(["picker:manage_sessions"])),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, current_user.tenant_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Pick session not found")
    session = await update_session(db, session, payload)
    await db.commit()
    session = await get_session(db, current_user.tenant_id, session_id)
    return _session_out(session)


@router.delete("/sessions/{session_id}", status_code=204)
async def delete(
    session_id: UUID,
    current_user=Depends(require_permissions(["picker:manage_sessions"])),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, current_user.tenant_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Pick session not found")
    session.status = "CANCELLED"
    await db.commit()
    return Response(status_code=204)


@router.get("/sessions/{session_id}/route", response_model=list[PickRouteItem])
async def route(
    session_id: UUID,
    current_user=Depends(require_permissions(["picker:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await build_route(db, current_user.tenant_id, session_id)


@router.post("/sessions/{session_id}/pick", response_model=PickEventOut)
async def pick(
    session_id: UUID,
    payload: PickEventCreate,
    current_user=Depends(require_permissions(["picker:pick"])),
    ctx=Depends(get_audit_context),
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, current_user.tenant_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Pick session not found")
    try:
        event = await record_event(db, session, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await create_audit_log(
        db,
        ctx,
        action="picker.pick_event",
        entity_type="pick_event",
        entity_id=event.id,
        before_state=None,
        after_state=serialize_model(event),
    )
    await db.commit()
    return event


@router.get("/sessions/{session_id}/events", response_model=list[PickEventOut])
async def events(
    session_id: UUID,
    current_user=Depends(require_permissions(["picker:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_events(db, current_user.tenant_id, session_id)
