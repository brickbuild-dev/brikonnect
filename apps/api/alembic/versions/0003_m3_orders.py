"""M3 orders tables.

Revision ID: 0003_m3_orders
Revises: 0002_m2_inventory
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_m3_orders"
down_revision = "0002_m2_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
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
        sa.Column("store_id", postgresql.UUID(as_uuid=True)),
        sa.Column("external_order_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'NEW'")),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("buyer_name", sa.String(length=200)),
        sa.Column("buyer_email", sa.String(length=320)),
        sa.Column("buyer_username", sa.String(length=100)),
        sa.Column("ship_to", postgresql.JSONB),
        sa.Column("shipping_method", sa.String(length=50)),
        sa.Column("subtotal", sa.Numeric(12, 2)),
        sa.Column("shipping_cost", sa.Numeric(12, 2)),
        sa.Column("tax_amount", sa.Numeric(12, 2)),
        sa.Column("discount_amount", sa.Numeric(12, 2)),
        sa.Column("grand_total", sa.Numeric(12, 2)),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column("ordered_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("shipped_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("store_id", "external_order_id", name="uq_orders_store_external"),
    )
    op.create_index("idx_orders_tenant", "orders", ["tenant_id"])
    op.create_index("idx_orders_status", "orders", ["tenant_id", "status"])
    op.create_index("idx_orders_date", "orders", ["tenant_id", "ordered_at"])

    op.create_table(
        "order_lines",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "inventory_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("inventory_items.id", ondelete="SET NULL"),
        ),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("item_no", sa.String(length=64), nullable=False),
        sa.Column("color_id", sa.Integer),
        sa.Column("color_name", sa.String(length=50)),
        sa.Column("condition", sa.String(length=10)),
        sa.Column("description", sa.Text),
        sa.Column("qty_ordered", sa.Integer, nullable=False),
        sa.Column("qty_picked", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("qty_missing", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("unit_price", sa.Numeric(12, 4)),
        sa.Column("line_total", sa.Numeric(12, 2)),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_order_lines_order", "order_lines", ["order_id"])
    op.create_index("idx_order_lines_inventory", "order_lines", ["inventory_item_id"])

    op.create_table(
        "order_status_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(length=30)),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column(
            "changed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("notes", sa.Text),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_order_status_events_order", "order_status_events", ["order_id"])


def downgrade() -> None:
    op.drop_index("idx_order_status_events_order", table_name="order_status_events")
    op.drop_table("order_status_events")
    op.drop_index("idx_order_lines_inventory", table_name="order_lines")
    op.drop_index("idx_order_lines_order", table_name="order_lines")
    op.drop_table("order_lines")
    op.drop_index("idx_orders_date", table_name="orders")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_index("idx_orders_tenant", table_name="orders")
    op.drop_table("orders")
