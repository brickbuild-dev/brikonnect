"""Brickognize cache table.

Revision ID: 0009_brickognize
Revises: 0008_catalog
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_brickognize"
down_revision = "0008_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brickognize_cache",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("image_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("predictions", postgresql.JSONB, nullable=False),
        sa.Column("top_prediction_item_no", sa.String(length=64)),
        sa.Column("top_prediction_confidence", sa.Numeric(4, 3)),
        sa.Column(
            "matched_catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("catalog_items.id"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_brickognize_hash", "brickognize_cache", ["image_hash"])


def downgrade() -> None:
    op.drop_index("idx_brickognize_hash", table_name="brickognize_cache")
    op.drop_table("brickognize_cache")
