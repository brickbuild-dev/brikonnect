"""M4 picker tables.

Revision ID: 0004_m4_picker
Revises: 0003_m3_orders
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_m4_picker"
down_revision = "0003_m3_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pick_sessions",
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
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column("total_orders", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("total_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("picked_items", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_pick_sessions_tenant", "pick_sessions", ["tenant_id"])
    op.create_index("idx_pick_sessions_status", "pick_sessions", ["tenant_id", "status"])

    op.create_table(
        "pick_session_orders",
        sa.Column(
            "pick_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pick_sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("batch_code", sa.String(length=10)),
    )

    op.create_table(
        "pick_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "pick_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pick_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "order_line_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("order_lines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False),
        sa.Column("location_code", sa.String(length=30)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_pick_events_session", "pick_events", ["pick_session_id"])


def downgrade() -> None:
    op.drop_index("idx_pick_events_session", table_name="pick_events")
    op.drop_table("pick_events")
    op.drop_table("pick_session_orders")
    op.drop_index("idx_pick_sessions_status", table_name="pick_sessions")
    op.drop_index("idx_pick_sessions_tenant", table_name="pick_sessions")
    op.drop_table("pick_sessions")
