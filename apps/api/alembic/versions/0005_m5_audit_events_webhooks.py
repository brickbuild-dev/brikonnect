"""M5 audit, events, webhooks tables.

Revision ID: 0005_m5_audit
Revises: 0004_m4_picker
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_m5_audit"
down_revision = "0004_m4_picker"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_name", sa.String(length=100)),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("before_state", postgresql.JSONB),
        sa.Column("after_state", postgresql.JSONB),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True)),
        sa.Column("request_id", postgresql.UUID(as_uuid=True)),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_tenant", "audit_log", ["tenant_id"])
    op.create_index("idx_audit_entity", "audit_log", ["tenant_id", "entity_type", "entity_id"])
    op.create_index("idx_audit_date", "audit_log", ["tenant_id", "created_at"])

    op.create_table(
        "events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_events_tenant_type", "events", ["tenant_id", "event_type"])
    op.create_index(
        "idx_events_unprocessed",
        "events",
        ["tenant_id"],
        postgresql_where=sa.text("processed_at IS NULL"),
    )

    op.create_table(
        "webhooks",
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
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("secret", sa.String(length=64), nullable=False),
        sa.Column("events", postgresql.ARRAY(sa.Text), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_webhooks_tenant", "webhooks", ["tenant_id"])

    op.create_table(
        "webhook_deliveries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "webhook_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("webhooks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("attempts", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("response_status", sa.Integer),
        sa.Column("response_body", sa.Text),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "idx_webhook_deliveries_pending",
        "webhook_deliveries",
        ["next_retry_at"],
        postgresql_where=sa.text("status = 'PENDING'"),
    )


def downgrade() -> None:
    op.drop_index("idx_webhook_deliveries_pending", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("idx_webhooks_tenant", table_name="webhooks")
    op.drop_table("webhooks")
    op.drop_index("idx_events_unprocessed", table_name="events")
    op.drop_index("idx_events_tenant_type", table_name="events")
    op.drop_table("events")
    op.drop_index("idx_audit_date", table_name="audit_log")
    op.drop_index("idx_audit_entity", table_name="audit_log")
    op.drop_index("idx_audit_tenant", table_name="audit_log")
    op.drop_table("audit_log")
