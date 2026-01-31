from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.locations.schemas import LocationOut


class InventoryLocationPayload(BaseModel):
    location_id: UUID
    qty: int = Field(ge=0)


class InventoryItemBase(BaseModel):
    item_type: str = Field(min_length=1, max_length=20)
    item_no: str = Field(min_length=1, max_length=64)
    color_id: int | None = None
    condition: str = Field(min_length=1, max_length=10)
    qty_available: int = 0
    qty_reserved: int = 0
    unit_price: Decimal | None = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    cost_basis: Decimal | None = None
    description: str | None = None
    remarks: str | None = None
    is_retain: bool = False
    is_stock_room: bool = False


class InventoryItemCreate(InventoryItemBase):
    locations: list[InventoryLocationPayload] | None = None


class InventoryItemUpdate(BaseModel):
    item_type: str | None = Field(default=None, max_length=20)
    item_no: str | None = Field(default=None, max_length=64)
    color_id: int | None = None
    condition: str | None = Field(default=None, max_length=10)
    qty_available: int | None = None
    qty_reserved: int | None = None
    unit_price: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    cost_basis: Decimal | None = None
    description: str | None = None
    remarks: str | None = None
    is_retain: bool | None = None
    is_stock_room: bool | None = None
    version: int | None = None
    locations: list[InventoryLocationPayload] | None = None


class InventoryItemLocationOut(BaseModel):
    location: LocationOut
    qty: int

    model_config = {"from_attributes": True}


class InventoryItemOut(InventoryItemBase):
    id: UUID
    tenant_id: UUID
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    locations: list[InventoryItemLocationOut] = []

    model_config = {"from_attributes": True}


class InventoryBulkItem(BaseModel):
    id: UUID | None = None
    item_type: str | None = Field(default=None, max_length=20)
    item_no: str | None = Field(default=None, max_length=64)
    color_id: int | None = None
    condition: str | None = Field(default=None, max_length=10)
    qty_available: int | None = None
    qty_reserved: int | None = None
    unit_price: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    cost_basis: Decimal | None = None
    description: str | None = None
    remarks: str | None = None
    is_retain: bool | None = None
    is_stock_room: bool | None = None
    version: int | None = None
    locations: list[InventoryLocationPayload] | None = None


class InventoryBulkRequest(BaseModel):
    items: list[InventoryBulkItem]
