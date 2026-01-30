from __future__ import annotations

from sqlalchemy import String, DateTime, BigInteger, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
