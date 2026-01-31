from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderLineBase(BaseModel):
    item_type: str = Field(min_length=1, max_length=20)
    item_no: str = Field(min_length=1, max_length=64)
    color_id: int | None = None
    color_name: str | None = None
    condition: str | None = None
    description: str | None = None
    qty_ordered: int = Field(ge=1)
    unit_price: Decimal | None = None
    line_total: Decimal | None = None


class OrderLineCreate(OrderLineBase):
    inventory_item_id: UUID | None = None


class OrderLineOut(OrderLineBase):
    id: UUID
    order_id: UUID
    tenant_id: UUID
    qty_picked: int
    qty_missing: int
    status: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderBase(BaseModel):
    external_order_id: str = Field(min_length=1, max_length=64)
    store_id: UUID | None = None
    buyer_name: str | None = None
    buyer_email: str | None = None
    buyer_username: str | None = None
    ship_to: dict | None = None
    shipping_method: str | None = None
    subtotal: Decimal | None = None
    shipping_cost: Decimal | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    grand_total: Decimal | None = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    ordered_at: datetime | None = None
    paid_at: datetime | None = None
    shipped_at: datetime | None = None


class OrderCreate(OrderBase):
    status: str = "NEW"
    lines: list[OrderLineCreate] = Field(default_factory=list)


class OrderUpdate(BaseModel):
    buyer_name: str | None = None
    buyer_email: str | None = None
    buyer_username: str | None = None
    ship_to: dict | None = None
    shipping_method: str | None = None
    subtotal: Decimal | None = None
    shipping_cost: Decimal | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    grand_total: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    ordered_at: datetime | None = None
    paid_at: datetime | None = None
    shipped_at: datetime | None = None


class OrderStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)
    notes: str | None = None


class OrderStatusEventOut(BaseModel):
    id: UUID
    from_status: str | None
    to_status: str
    changed_by: UUID | None = None
    notes: str | None = None
    changed_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderOut(OrderBase):
    id: UUID
    tenant_id: UUID
    status: str
    status_changed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    lines: list[OrderLineOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
