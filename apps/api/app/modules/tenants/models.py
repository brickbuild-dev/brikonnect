from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import JSONBCompatible


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'free'"))
    settings: Mapped[dict] = mapped_column(
        JSONBCompatible,
        nullable=False,
        server_default=text("'{}'"),
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'EUR'"))
    current_version: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'full'"),
    )
    has_brikick_store: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    billing_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        server_default=text("'EUR'"),
    )
    billing_email: Mapped[str | None] = mapped_column(String(320))
    billing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100))
    paypal_payer_id: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=func.now(),
    )

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
