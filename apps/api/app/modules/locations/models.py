from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_locations_tenant_code"),)

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
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    zone: Mapped[str | None] = mapped_column(String(20))
    aisle: Mapped[str | None] = mapped_column(String(10))
    shelf: Mapped[str | None] = mapped_column(String(10))
    bin: Mapped[str | None] = mapped_column(String(10))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    items = relationship("InventoryItemLocation", back_populates="location", cascade="all, delete-orphan")
