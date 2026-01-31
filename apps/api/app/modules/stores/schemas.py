from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StoreBase(BaseModel):
    channel: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=100)
    is_enabled: bool = True
    is_primary: bool = False
    settings: dict = Field(default_factory=dict)


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    is_enabled: bool | None = None
    is_primary: bool | None = None
    settings: dict | None = None


class StoreOut(StoreBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class StoreCredentialsPayload(BaseModel):
    data: dict = Field(default_factory=dict)
