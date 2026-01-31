from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobRun(Base):
    __tablename__ = "job_runs"
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key", name="uq_job_runs_idempotency"),)

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
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'PENDING'"))

    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    progress_message: Mapped[str | None] = mapped_column(Text)
    progress_data: Mapped[dict | None] = mapped_column(JSONB)

    idempotency_key: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    last_heartbeat_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))

    error_message: Mapped[str | None] = mapped_column(Text)
    result: Mapped[dict | None] = mapped_column(JSONB)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
