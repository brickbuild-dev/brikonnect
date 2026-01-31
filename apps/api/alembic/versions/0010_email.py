"""Email templates, queue, notifications.

Revision ID: 0010_email
Revises: 0009_brickognize
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_email"
down_revision = "0009_brickognize"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_templates",
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
        ),
        sa.Column("template_key", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("body_html", sa.Text, nullable=False),
        sa.Column("body_text", sa.Text),
        sa.Column("variables", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "template_key", name="uq_email_templates_tenant_key"),
    )

    op.create_table(
        "email_queue",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id")),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("to_name", sa.String(length=100)),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("body_html", sa.Text, nullable=False),
        sa.Column("body_text", sa.Text),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'PENDING'")),
        sa.Column("attempts", sa.Integer, server_default=sa.text("0")),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column("template_key", sa.String(length=50)),
        sa.Column("reference_type", sa.String(length=50)),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_email_queue_pending",
        "email_queue",
        ["status"],
        postgresql_where=sa.text("status = 'PENDING'"),
    )

    op.create_table(
        "notifications",
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
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text),
        sa.Column("action_url", sa.Text),
        sa.Column("action_label", sa.String(length=50)),
        sa.Column("reference_type", sa.String(length=50)),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("dismissed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_notifications_user", "notifications", ["tenant_id", "user_id", "read_at"])


def downgrade() -> None:
    op.drop_index("idx_notifications_user", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("idx_email_queue_pending", table_name="email_queue")
    op.drop_table("email_queue")
    op.drop_table("email_templates")
