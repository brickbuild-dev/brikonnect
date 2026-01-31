from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EmailTemplateCreate(BaseModel):
    template_key: str = Field(min_length=1, max_length=50)
    subject: str = Field(min_length=1, max_length=200)
    body_html: str
    body_text: str | None = None
    variables: list[str] | None = None
    is_active: bool = True


class EmailTemplateOut(EmailTemplateCreate):
    id: UUID
    tenant_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class EmailQueueOut(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    to_email: str
    to_name: str | None = None
    subject: str
    body_html: str
    body_text: str | None = None
    status: str
    attempts: int
    last_attempt_at: datetime | None = None
    sent_at: datetime | None = None
    error_message: str | None = None
    template_key: str | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
