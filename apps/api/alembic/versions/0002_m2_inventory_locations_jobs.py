"""M2 inventory + locations + jobs tables.

Revision ID: 0002_m2_inventory
Revises: 0001_m1_auth
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_m2_inventory"
down_revision = "0001_m1_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_no", sa.String(length=64), nullable=False),
        sa.Column("color_id", sa.Integer),
        sa.Column("condition", sa.String(length=10), nullable=False),
        sa.Column("qty_available", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("qty_reserved", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("unit_price", sa.Numeric(12, 4)),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column("cost_basis", sa.Numeric(12, 4)),
        sa.Column("description", sa.Text),
        sa.Column("remarks", sa.Text),
        sa.Column("is_retain", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_stock_room", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_inventory_tenant", "inventory_items", ["tenant_id"])
    op.create_index(
        "idx_inventory_lookup",
        "inventory_items",
        ["tenant_id", "item_type", "item_no", "color_id", "condition"],
    )

    op.create_table(
        "locations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("zone", sa.String(length=20)),
        sa.Column("aisle", sa.String(length=10)),
        sa.Column("shelf", sa.String(length=10)),
        sa.Column("bin", sa.String(length=10)),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_locations_tenant_code"),
    )
    op.create_index("idx_locations_tenant", "locations", ["tenant_id"])

    op.create_table(
        "inventory_item_locations",
        sa.Column(
            "inventory_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("qty", sa.Integer, nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "job_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("progress_percent", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("progress_message", sa.Text),
        sa.Column("progress_data", postgresql.JSONB),
        sa.Column("idempotency_key", sa.String(length=100)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("result", postgresql.JSONB),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_job_runs_idempotency"),
    )
    op.create_index("idx_job_runs_tenant", "job_runs", ["tenant_id"])
    op.create_index("idx_job_runs_status", "job_runs", ["status"])


def downgrade() -> None:
    op.drop_index("idx_job_runs_status", table_name="job_runs")
    op.drop_index("idx_job_runs_tenant", table_name="job_runs")
    op.drop_table("job_runs")
    op.drop_table("inventory_item_locations")
    op.drop_index("idx_locations_tenant", table_name="locations")
    op.drop_table("locations")
    op.drop_index("idx_inventory_lookup", table_name="inventory_items")
    op.drop_index("idx_inventory_tenant", table_name="inventory_items")
    op.drop_table("inventory_items")
