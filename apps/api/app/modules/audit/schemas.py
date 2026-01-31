from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: UUID
    tenant_id: UUID
    actor_type: str
    actor_id: UUID | None = None
    actor_name: str | None = None
    action: str
    entity_type: str
    entity_id: UUID | None = None
    before_state: dict | None = None
    after_state: dict | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuditRevertResponse(BaseModel):
    reverted: bool
    entity_id: UUID | None = None
