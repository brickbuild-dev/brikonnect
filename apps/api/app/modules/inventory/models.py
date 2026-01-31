from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

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

    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(64), nullable=False)
    color_id: Mapped[int | None] = mapped_column(Integer)
    condition: Mapped[str] = mapped_column(String(10), nullable=False)

    qty_available: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    qty_reserved: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'EUR'"))
    cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))

    description: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)
    is_retain: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_stock_room: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=func.now(),
    )

    locations = relationship(
        "InventoryItemLocation",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    def key(self) -> tuple[str, str, int | None, str]:
        return (self.item_type, self.item_no, self.color_id, self.condition)


class InventoryItemLocation(Base):
    __tablename__ = "inventory_item_locations"

    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    item = relationship("InventoryItem", back_populates="locations")
    location = relationship("Location", back_populates="items")


class InventoryExternalId(Base):
    __tablename__ = "inventory_external_ids"
    __table_args__ = (
        UniqueConstraint("store_id", "external_lot_id", name="uq_inventory_ext_store_lot"),
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
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_lot_id: Mapped[str | None] = mapped_column(String(64))
    external_inventory_id: Mapped[str | None] = mapped_column(String(64))
    last_synced_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
