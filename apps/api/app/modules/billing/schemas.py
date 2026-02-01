from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BillingStatusOut(BaseModel):
    current_version: str
    has_brikick_discount: bool
    current_rate: Decimal
    billing_status: str
    current_month_gmv: Decimal
    current_month_estimated_fee: Decimal


class BillingVersionRequest(BaseModel):
    version: str = Field(min_length=1, max_length=10)
    reason: str | None = Field(default=None, max_length=100)


class InvoiceOut(BaseModel):
    id: UUID
    tenant_id: UUID
    period_start: date
    period_end: date
    year_month: str
    currency: str
    net_gmv: Decimal
    lite_days: int
    lite_gmv: Decimal
    lite_fee: Decimal
    full_days: int
    full_gmv: Decimal
    full_fee: Decimal
    brikick_discount_applied: bool
    subtotal: Decimal
    accumulated_from_previous: Decimal
    total_due: Decimal
    minimum_threshold: Decimal
    below_minimum: bool
    status: str
    issued_at: datetime | None = None
    due_date: date | None = None
    paid_at: datetime | None = None
    payment_method: str | None = None
    payment_reference: str | None = None
    store_breakdown: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class InvoicePayRequest(BaseModel):
    method: str = Field(min_length=1, max_length=20)
    payment_method_id: UUID | None = None


class PaymentOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    amount: Decimal
    currency: str
    method: str
    status: str
    stripe_payment_intent_id: str | None = None
    stripe_charge_id: str | None = None
    paypal_order_id: str | None = None
    paypal_capture_id: str | None = None
    card_last4: str | None = None
    card_brand: str | None = None
    error_message: str | None = None
    processed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PaymentMethodCreate(BaseModel):
    method_type: str = Field(min_length=1, max_length=20)
    stripe_customer_id: str | None = None
    stripe_payment_method_id: str | None = None
    paypal_payer_id: str | None = None
    card_last4: str | None = None
    card_brand: str | None = None
    card_exp_month: int | None = None
    card_exp_year: int | None = None
    paypal_email: str | None = None
    is_default: bool = False


class PaymentMethodOut(BaseModel):
    id: UUID
    tenant_id: UUID
    method_type: str
    is_default: bool
    stripe_customer_id: str | None = None
    stripe_payment_method_id: str | None = None
    paypal_payer_id: str | None = None
    card_last4: str | None = None
    card_brand: str | None = None
    card_exp_month: int | None = None
    card_exp_year: int | None = None
    paypal_email: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
