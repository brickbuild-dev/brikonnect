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
from app.db.types import ArrayOfStrings, JSONBCompatible


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (
        UniqueConstraint("item_type", "item_no", name="uq_catalog_items_type_no"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category_id: Mapped[int | None] = mapped_column(Integer)
    category_name: Mapped[str | None] = mapped_column(String(200))
    weight_grams: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    dimensions: Mapped[dict | None] = mapped_column(JSONBCompatible)
    image_url: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    year_released: Mapped[int | None] = mapped_column(Integer)
    year_ended: Mapped[int | None] = mapped_column(Integer)
    alternate_nos: Mapped[list[str] | None] = mapped_column(ArrayOfStrings)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_updated_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=func.now(),
    )


class CatalogColor(Base):
    __tablename__ = "catalog_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rgb: Mapped[str | None] = mapped_column(String(6))
    brickowl_id: Mapped[int | None] = mapped_column(Integer)
    rebrickable_id: Mapped[int | None] = mapped_column(Integer)
    ldraw_id: Mapped[int | None] = mapped_column(Integer)
    lego_ids: Mapped[list[int] | None] = mapped_column(JSONBCompatible)
    color_type: Mapped[str | None] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(20), server_default=text("'bricklink'"))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=func.now(),
    )


class CatalogCategory(Base):
    __tablename__ = "catalog_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("catalog_categories.id"))
    source: Mapped[str] = mapped_column(String(20), server_default=text("'bricklink'"))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class CatalogIdMapping(Base):
    __tablename__ = "catalog_id_mappings"
    __table_args__ = (
        UniqueConstraint("item_type", "canonical_item_no", name="uq_catalog_mapping_type_no"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    canonical_item_no: Mapped[str] = mapped_column(String(64), nullable=False)
    bricklink_id: Mapped[str | None] = mapped_column(String(64))
    brickowl_id: Mapped[str | None] = mapped_column(String(64))
    brikick_id: Mapped[str | None] = mapped_column(String(64))
    rebrickable_id: Mapped[str | None] = mapped_column(String(64))
    lego_element_ids: Mapped[list[str] | None] = mapped_column(ArrayOfStrings)
    mapping_source: Mapped[str | None] = mapped_column(String(20))
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), server_default=text("1.0"))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=func.now(),
    )


class CatalogItemColor(Base):
    __tablename__ = "catalog_item_colors"

    item_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    item_no: Mapped[str] = mapped_column(String(64), primary_key=True)
    color_id: Mapped[int] = mapped_column(Integer, ForeignKey("catalog_colors.id"), primary_key=True)
    qty_known: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20), server_default=text("'bricklink'"))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class CatalogSetItem(Base):
    __tablename__ = "catalog_set_items"

    set_no: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20), primary_key=True)
    item_no: Mapped[str] = mapped_column(String(64), primary_key=True)
    color_id: Mapped[int] = mapped_column(Integer, ForeignKey("catalog_colors.id"), primary_key=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    is_spare: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), primary_key=True)
    is_counterpart: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    source: Mapped[str] = mapped_column(String(20), server_default=text("'rebrickable'"))
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class ApiRateLimit(Base):
    __tablename__ = "api_rate_limits"

    source: Mapped[str] = mapped_column(String(30), primary_key=True)
    daily_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    requests_today: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    last_request_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    reset_at: Mapped[object | None] = mapped_column(Date)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )
