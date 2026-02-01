from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBCompatible


class TenantVersionHistory(Base):
    __tablename__ = "tenant_version_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(10), nullable=False)
    started_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    ended_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    change_reason: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "year_month", name="uq_invoices_tenant_month"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    period_start: Mapped[object] = mapped_column(Date, nullable=False)
    period_end: Mapped[object] = mapped_column(Date, nullable=False)
    year_month: Mapped[str] = mapped_column(String(7), nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    net_gmv: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    lite_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    lite_gmv: Mapped[Decimal] = mapped_column(Numeric(12, 2), server_default=text("0"))
    lite_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default=text("0"))

    full_days: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    full_gmv: Mapped[Decimal] = mapped_column(Numeric(12, 2), server_default=text("0"))
    full_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default=text("0"))

    brikick_discount_applied: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    accumulated_from_previous: Mapped[Decimal] = mapped_column(Numeric(10, 2), server_default=text("0"))
    total_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    minimum_threshold: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    below_minimum: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'DRAFT'"))
    issued_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[object | None] = mapped_column(Date)
    paid_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))

    payment_method: Mapped[str | None] = mapped_column(String(20))
    payment_reference: Mapped[str | None] = mapped_column(String(100))

    store_breakdown: Mapped[dict | None] = mapped_column(JSONBCompatible)

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=func.now(),
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)

    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(100))
    stripe_charge_id: Mapped[str | None] = mapped_column(String(100))
    paypal_order_id: Mapped[str | None] = mapped_column(String(100))
    paypal_capture_id: Mapped[str | None] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(String(20), nullable=False)

    card_last4: Mapped[str | None] = mapped_column(String(4))
    card_brand: Mapped[str | None] = mapped_column(String(20))

    error_message: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "stripe_payment_method_id", name="uq_payment_methods_stripe"),
        UniqueConstraint("tenant_id", "paypal_payer_id", name="uq_payment_methods_paypal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    method_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))

    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    stripe_payment_method_id: Mapped[str | None] = mapped_column(String(100))

    paypal_payer_id: Mapped[str | None] = mapped_column(String(100))

    card_last4: Mapped[str | None] = mapped_column(String(4))
    card_brand: Mapped[str | None] = mapped_column(String(20))
    card_exp_month: Mapped[int | None] = mapped_column(Integer)
    card_exp_year: Mapped[int | None] = mapped_column(Integer)

    paypal_email: Mapped[str | None] = mapped_column(String(320))

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class BillingAccumulated(Base):
    __tablename__ = "billing_accumulated"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default=text("0"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'EUR'"))
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
