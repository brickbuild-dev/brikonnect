from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PickSessionCreate(BaseModel):
    order_ids: list[UUID] = Field(min_length=1)
    notes: str | None = None


class PickSessionUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class PickSessionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    created_by: UUID
    status: str
    total_orders: int
    total_items: int
    picked_items: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None
    order_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PickEventCreate(BaseModel):
    order_line_id: UUID
    event_type: str = Field(min_length=1, max_length=20)
    qty: int = Field(ge=1)
    location_code: str | None = None
    notes: str | None = None


class PickEventOut(BaseModel):
    id: UUID
    pick_session_id: UUID
    order_line_id: UUID
    user_id: UUID
    event_type: str
    qty: int
    location_code: str | None = None
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PickRouteItem(BaseModel):
    order_id: UUID
    order_line_id: UUID
    item_no: str
    qty_ordered: int
    location_code: str | None = None
