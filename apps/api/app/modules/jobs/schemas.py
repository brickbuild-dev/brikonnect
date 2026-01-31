from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobOut(BaseModel):
    id: UUID
    tenant_id: UUID
    job_type: str
    status: str
    progress_percent: int
    progress_message: str | None = None
    progress_data: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
