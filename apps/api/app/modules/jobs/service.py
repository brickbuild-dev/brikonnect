from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.models import JobRun


async def create_job(
    db: AsyncSession,
    tenant_id,
    job_type: str,
    created_by=None,
    idempotency_key: str | None = None,
) -> JobRun:
    job = JobRun(
        tenant_id=tenant_id,
        job_type=job_type,
        created_by=created_by,
        idempotency_key=idempotency_key,
    )
    db.add(job)
    await db.flush()
    return job


async def get_job(db: AsyncSession, tenant_id, job_id) -> JobRun | None:
    result = await db.execute(
        select(JobRun).where(JobRun.tenant_id == tenant_id, JobRun.id == job_id)
    )
    return result.scalar_one_or_none()
