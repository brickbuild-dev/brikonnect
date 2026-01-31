from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("store_id", "external_order_id", name="uq_orders_store_external"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    external_order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'NEW'"))
    status_changed_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    buyer_name: Mapped[str | None] = mapped_column(String(200))
    buyer_email: Mapped[str | None] = mapped_column(String(320))
    buyer_username: Mapped[str | None] = mapped_column(String(100))

    ship_to: Mapped[dict | None] = mapped_column(JSONB)
    shipping_method: Mapped[str | None] = mapped_column(String(50))

    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    shipping_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    grand_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'EUR'"))

    ordered_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=func.now(),
    )

    lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")
    status_events = relationship(
        "OrderStatusEvent", back_populates="order", cascade="all, delete-orphan"
    )


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inventory_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="SET NULL"),
    )

    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(64), nullable=False)
    color_id: Mapped[int | None] = mapped_column(Integer)
    color_name: Mapped[str | None] = mapped_column(String(50))
    condition: Mapped[str | None] = mapped_column(String(10))
    description: Mapped[str | None] = mapped_column(Text)

    qty_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_picked: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    qty_missing: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    line_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'PENDING'"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    order = relationship("Order", back_populates="lines")


class OrderStatusEvent(Base):
    __tablename__ = "order_status_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    notes: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    order = relationship("Order", back_populates="status_events")
