from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.audit.deps import get_audit_context
from app.modules.audit.service import AuditContext
from app.modules.rbac.deps import require_permissions
from app.modules.sync.schemas import (
    SyncApproveResponse,
    SyncPlanItemOut,
    SyncPreviewRequest,
    SyncPreviewResponse,
    SyncRunOut,
)
from app.modules.sync.service import approve_run, cancel_run, create_preview, get_run, list_plan_items, list_runs

router = APIRouter()


@router.post("/preview", response_model=SyncPreviewResponse)
async def preview(
    payload: SyncPreviewRequest,
    current_user=Depends(require_permissions(["sync:preview"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        run = await create_preview(db, current_user.tenant_id, current_user.id, payload)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"run": run}


@router.get("/runs", response_model=list[SyncRunOut])
async def list_sync_runs(
    current_user=Depends(require_permissions(["sync:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_runs(db, current_user.tenant_id)


@router.get("/runs/{run_id}", response_model=SyncRunOut)
async def get_sync_run(
    run_id: UUID,
    current_user=Depends(require_permissions(["sync:read"])),
    db: AsyncSession = Depends(get_db),
):
    run = await get_run(db, current_user.tenant_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Sync run not found")
    return run


@router.get("/runs/{run_id}/plan", response_model=list[SyncPlanItemOut])
async def get_sync_plan(
    run_id: UUID,
    current_user=Depends(require_permissions(["sync:read"])),
    db: AsyncSession = Depends(get_db),
):
    run = await get_run(db, current_user.tenant_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Sync run not found")
    return await list_plan_items(db, run)


@router.post("/runs/{run_id}/approve", response_model=SyncApproveResponse)
async def approve(
    run_id: UUID,
    audit_ctx: AuditContext = Depends(get_audit_context),
    current_user=Depends(require_permissions(["sync:apply"])),
    db: AsyncSession = Depends(get_db),
):
    run = await get_run(db, current_user.tenant_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Sync run not found")
    try:
        run = await approve_run(db, run, current_user.id, audit_ctx)
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"run": run}


@router.post("/runs/{run_id}/cancel", response_model=SyncRunOut)
async def cancel(
    run_id: UUID,
    current_user=Depends(require_permissions(["sync:apply"])),
    db: AsyncSession = Depends(get_db),
):
    run = await get_run(db, current_user.tenant_id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Sync run not found")
    run = await cancel_run(db, run)
    await db.commit()
    return run
