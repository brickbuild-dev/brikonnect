from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.jobs.schemas import JobOut
from app.modules.jobs.service import get_job
from app.modules.rbac.deps import require_permissions

router = APIRouter()


@router.get("/{job_id}", response_model=JobOut)
async def get_job_status(
    job_id: UUID,
    current_user=Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job(db, current_user.tenant_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: UUID,
    current_user=Depends(require_permissions(["inventory:read"])),
    db: AsyncSession = Depends(get_db),
):
    job = await get_job(db, current_user.tenant_id, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"lines": []}
