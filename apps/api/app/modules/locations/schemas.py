from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    zone: str | None = Field(default=None, max_length=20)
    aisle: str | None = Field(default=None, max_length=10)
    shelf: str | None = Field(default=None, max_length=10)
    bin: str | None = Field(default=None, max_length=10)
    sort_order: int = 0


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    code: str | None = Field(default=None, max_length=30)
    zone: str | None = Field(default=None, max_length=20)
    aisle: str | None = Field(default=None, max_length=10)
    shelf: str | None = Field(default=None, max_length=10)
    bin: str | None = Field(default=None, max_length=10)
    sort_order: int | None = None


class LocationOut(LocationBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
