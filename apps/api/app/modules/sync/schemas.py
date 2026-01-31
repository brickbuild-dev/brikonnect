from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SyncPreviewRequest(BaseModel):
    source_store_id: UUID
    target_store_id: UUID
    direction: str = Field(default="SOURCE_TO_TARGET", max_length=20)
    allow_large_removals: bool = False


class SyncRunOut(BaseModel):
    id: UUID
    tenant_id: UUID
    source_store_id: UUID
    target_store_id: UUID
    mode: str
    direction: str
    status: str
    plan_summary: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_by: UUID
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SyncPlanItemOut(BaseModel):
    id: UUID
    sync_run_id: UUID
    action: str
    skip_reason: str | None = None
    inventory_item_id: UUID | None = None
    source_external_id: str | None = None
    target_external_id: str | None = None
    before_state: dict | None = None
    after_state: dict | None = None
    changes: list | None = None
    status: str
    error_message: str | None = None
    applied_at: datetime | None = None

    model_config = {"from_attributes": True}


class SyncApproveResponse(BaseModel):
    run: SyncRunOut


class SyncPreviewResponse(BaseModel):
    run: SyncRunOut
