from __future__ import annotations

from sqlalchemy import String, Integer, DateTime, BigInteger, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class InventoryLot(Base):
    __tablename__ = "inventory_lots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    sku: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    item_type: Mapped[str] = mapped_column(String(16), nullable=False)  # PART/SET/MINIFIG/...
    item_no: Mapped[str] = mapped_column(String(64), nullable=False)
    color_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    condition: Mapped[str] = mapped_column(String(16), nullable=False, server_default="USED")  # NEW/USED
    qty_available: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    price_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    location: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
