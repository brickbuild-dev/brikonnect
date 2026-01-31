from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WebhookBase(BaseModel):
    url: str
    events: list[str] = Field(default_factory=list)
    is_enabled: bool = True


class WebhookCreate(WebhookBase):
    secret: str | None = None


class WebhookUpdate(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    is_enabled: bool | None = None


class WebhookOut(WebhookBase):
    id: UUID
    tenant_id: UUID
    secret: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class WebhookDeliveryOut(BaseModel):
    id: UUID
    webhook_id: UUID
    event_id: UUID
    status: str
    attempts: int
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
