"""Catalog cache tables.

Revision ID: 0008_catalog
Revises: 0007_billing
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_catalog"
down_revision = "0007_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_no", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("category_id", sa.Integer),
        sa.Column("category_name", sa.String(length=200)),
        sa.Column("weight_grams", sa.Numeric(10, 2)),
        sa.Column("dimensions", postgresql.JSONB),
        sa.Column("image_url", sa.Text),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("year_released", sa.Integer),
        sa.Column("year_ended", sa.Integer),
        sa.Column("alternate_nos", postgresql.ARRAY(sa.Text)),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("item_type", "item_no", name="uq_catalog_items_type_no"),
    )
    op.create_index("idx_catalog_type_no", "catalog_items", ["item_type", "item_no"])
    op.create_index("idx_catalog_name", "catalog_items", ["name"])

    op.create_table(
        "catalog_colors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("rgb", sa.String(length=6)),
        sa.Column("brickowl_id", sa.Integer),
        sa.Column("rebrickable_id", sa.Integer),
        sa.Column("ldraw_id", sa.Integer),
        sa.Column("lego_ids", postgresql.ARRAY(sa.Integer)),
        sa.Column("color_type", sa.String(length=20)),
        sa.Column("source", sa.String(length=20), server_default=sa.text("'bricklink'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "catalog_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("catalog_categories.id")),
        sa.Column("source", sa.String(length=20), server_default=sa.text("'bricklink'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "catalog_id_mappings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("canonical_item_no", sa.String(length=64), nullable=False),
        sa.Column("bricklink_id", sa.String(length=64)),
        sa.Column("brickowl_id", sa.String(length=64)),
        sa.Column("brikick_id", sa.String(length=64)),
        sa.Column("rebrickable_id", sa.String(length=64)),
        sa.Column("lego_element_ids", postgresql.ARRAY(sa.Text)),
        sa.Column("mapping_source", sa.String(length=20)),
        sa.Column("confidence", sa.Numeric(3, 2), server_default=sa.text("1.0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("item_type", "canonical_item_no", name="uq_catalog_mapping_type_no"),
    )
    op.create_index("idx_mapping_bricklink", "catalog_id_mappings", ["bricklink_id"])
    op.create_index("idx_mapping_brickowl", "catalog_id_mappings", ["brickowl_id"])
    op.create_index("idx_mapping_brikick", "catalog_id_mappings", ["brikick_id"])
    op.create_index("idx_mapping_rebrickable", "catalog_id_mappings", ["rebrickable_id"])

    op.create_table(
        "catalog_item_colors",
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_no", sa.String(length=64), nullable=False),
        sa.Column("color_id", sa.Integer, sa.ForeignKey("catalog_colors.id"), nullable=False),
        sa.Column("qty_known", sa.Integer),
        sa.Column("source", sa.String(length=20), server_default=sa.text("'bricklink'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("item_type", "item_no", "color_id"),
    )

    op.create_table(
        "catalog_set_items",
        sa.Column("set_no", sa.String(length=64), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_no", sa.String(length=64), nullable=False),
        sa.Column("color_id", sa.Integer, sa.ForeignKey("catalog_colors.id")),
        sa.Column("qty", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("is_spare", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_counterpart", sa.Boolean, server_default=sa.text("false")),
        sa.Column("source", sa.String(length=20), server_default=sa.text("'rebrickable'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("set_no", "item_type", "item_no", "color_id", "is_spare"),
    )

    op.create_table(
        "api_rate_limits",
        sa.Column("source", sa.String(length=30), primary_key=True),
        sa.Column("daily_limit", sa.Integer, nullable=False),
        sa.Column("requests_today", sa.Integer, server_default=sa.text("0")),
        sa.Column("last_request_at", sa.DateTime(timezone=True)),
        sa.Column("reset_at", sa.Date),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("api_rate_limits")
    op.drop_table("catalog_set_items")
    op.drop_table("catalog_item_colors")
    op.drop_index("idx_mapping_rebrickable", table_name="catalog_id_mappings")
    op.drop_index("idx_mapping_brikick", table_name="catalog_id_mappings")
    op.drop_index("idx_mapping_brickowl", table_name="catalog_id_mappings")
    op.drop_index("idx_mapping_bricklink", table_name="catalog_id_mappings")
    op.drop_table("catalog_id_mappings")
    op.drop_table("catalog_categories")
    op.drop_table("catalog_colors")
    op.drop_index("idx_catalog_name", table_name="catalog_items")
    op.drop_index("idx_catalog_type_no", table_name="catalog_items")
    op.drop_table("catalog_items")
