from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ShippingCarrierConfigCreate(BaseModel):
    carrier_code: str = Field(min_length=1, max_length=30)
    credentials: dict | None = None
    is_enabled: bool = True


class ShippingCarrierConfigOut(BaseModel):
    id: UUID
    tenant_id: UUID
    carrier_code: str
    credentials: dict | None = None
    is_enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ShippingRatesRequest(BaseModel):
    order_id: UUID
    carrier_codes: list[str] | None = None


class ShippingRateOut(BaseModel):
    carrier_code: str
    service_level: str
    amount: str
    currency: str
    estimated_days: int | None = None


class CreateLabelRequest(BaseModel):
    order_id: UUID
    carrier_code: str
    service_level: str


class ShipmentOut(BaseModel):
    id: UUID
    tenant_id: UUID
    order_id: UUID
    carrier_code: str
    service_level: str
    status: str
    label_url: str | None = None
    tracking_number: str | None = None
    rate_amount: Decimal | None = None
    currency: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TrackingOut(BaseModel):
    tracking_number: str
    status: str
    carrier_code: str
    history: list[dict] | None = None
