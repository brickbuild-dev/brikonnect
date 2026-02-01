from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=200)
    plan: str = Field(default="free", max_length=20)
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    current_version: str = Field(default="full", max_length=10)
    has_brikick_store: bool = False
    billing_currency: str = Field(default="EUR", min_length=3, max_length=3)
    billing_email: str | None = None
    billing_status: str = Field(default="ACTIVE", max_length=20)
    stripe_customer_id: str | None = None
    paypal_payer_id: str | None = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    plan: str | None = Field(default=None, max_length=20)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    current_version: str | None = Field(default=None, max_length=10)
    has_brikick_store: bool | None = None
    billing_currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_email: str | None = None
    billing_status: str | None = Field(default=None, max_length=20)
    stripe_customer_id: str | None = None
    paypal_payer_id: str | None = None


class TenantOut(TenantBase):
    id: UUID
    settings: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
