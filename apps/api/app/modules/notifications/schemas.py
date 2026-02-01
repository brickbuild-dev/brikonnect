from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID | None = None
    type: str
    title: str
    body: str | None = None
    action_url: str | None = None
    action_label: str | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    read_at: datetime | None = None
    dismissed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
