from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBCompatible


class BrickognizeCache(Base):
    __tablename__ = "brickognize_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    image_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    predictions: Mapped[list] = mapped_column(JSONBCompatible, nullable=False)
    top_prediction_item_no: Mapped[str | None] = mapped_column(String(64))
    top_prediction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    matched_catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
