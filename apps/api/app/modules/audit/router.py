from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.audit.deps import get_audit_context
from app.modules.audit.schemas import AuditLogOut, AuditRevertResponse
from app.modules.audit.service import get_audit_log, list_audit_logs, revert_audit_log
from app.modules.rbac.deps import require_permissions

router = APIRouter()


@router.get("/", response_model=list[AuditLogOut])
async def list_logs(
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    current_user=Depends(require_permissions(["audit:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_audit_logs(db, current_user.tenant_id, entity_type, entity_id)


@router.post("/{audit_id}/revert", response_model=AuditRevertResponse)
async def revert(
    audit_id: UUID,
    ctx=Depends(get_audit_context),
    _user=Depends(require_permissions(["audit:read"])),
    db: AsyncSession = Depends(get_db),
):
    audit = await get_audit_log(db, ctx.tenant_id, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit log not found")
    try:
        await revert_audit_log(db, ctx, audit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return AuditRevertResponse(reverted=True, entity_id=audit.entity_id)
