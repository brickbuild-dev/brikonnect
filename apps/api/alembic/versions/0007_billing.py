"""Billing system tables.

Revision ID: 0007_billing
Revises: 0006_m6_sync
Create Date: 2026-01-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_billing"
down_revision = "0006_m6_sync"
branch_labels = None
depends_on = None


def upgrade() -> None:
    product_version = sa.Enum("lite", "full", name="product_version")
    product_version.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenant_version_history",
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
        sa.Column("version", product_version, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("change_reason", sa.String(length=100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_tenant_version_tenant", "tenant_version_history", ["tenant_id"])
    op.create_index(
        "idx_tenant_version_active",
        "tenant_version_history",
        ["tenant_id"],
        postgresql_where=sa.text("ended_at IS NULL"),
    )

    op.add_column(
        "tenants",
        sa.Column(
            "current_version",
            product_version,
            nullable=False,
            server_default=sa.text("'full'"),
        ),
    )
    op.add_column(
        "tenants",
        sa.Column("has_brikick_store", sa.Boolean, nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "tenants",
        sa.Column("billing_currency", sa.String(length=3), nullable=False, server_default=sa.text("'EUR'")),
    )
    op.add_column("tenants", sa.Column("billing_email", sa.String(length=320)))
    op.add_column(
        "tenants",
        sa.Column("billing_status", sa.String(length=20), nullable=False, server_default=sa.text("'ACTIVE'")),
    )
    op.add_column("tenants", sa.Column("stripe_customer_id", sa.String(length=100)))
    op.add_column("tenants", sa.Column("paypal_payer_id", sa.String(length=100)))

    op.create_table(
        "invoices",
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
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("year_month", sa.String(length=7), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("net_gmv", sa.Numeric(12, 2), nullable=False),
        sa.Column("lite_days", sa.Integer, server_default=sa.text("0")),
        sa.Column("lite_gmv", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("lite_fee", sa.Numeric(10, 2), server_default=sa.text("0")),
        sa.Column("full_days", sa.Integer, server_default=sa.text("0")),
        sa.Column("full_gmv", sa.Numeric(12, 2), server_default=sa.text("0")),
        sa.Column("full_fee", sa.Numeric(10, 2), server_default=sa.text("0")),
        sa.Column("brikick_discount_applied", sa.Boolean, server_default=sa.text("false")),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("accumulated_from_previous", sa.Numeric(10, 2), server_default=sa.text("0")),
        sa.Column("total_due", sa.Numeric(10, 2), nullable=False),
        sa.Column("minimum_threshold", sa.Numeric(10, 2), nullable=False),
        sa.Column("below_minimum", sa.Boolean, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("due_date", sa.Date),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("payment_method", sa.String(length=20)),
        sa.Column("payment_reference", sa.String(length=100)),
        sa.Column("store_breakdown", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "year_month", name="uq_invoices_tenant_month"),
    )
    op.create_index("idx_invoices_tenant", "invoices", ["tenant_id"])
    op.create_index("idx_invoices_status", "invoices", ["status"])
    op.create_index(
        "idx_invoices_due",
        "invoices",
        ["due_date"],
        postgresql_where=sa.text("status = 'ISSUED'"),
    )

    op.create_table(
        "payments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(length=100)),
        sa.Column("stripe_charge_id", sa.String(length=100)),
        sa.Column("paypal_order_id", sa.String(length=100)),
        sa.Column("paypal_capture_id", sa.String(length=100)),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("card_last4", sa.String(length=4)),
        sa.Column("card_brand", sa.String(length=20)),
        sa.Column("error_message", sa.Text),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_payments_invoice", "payments", ["invoice_id"])

    op.create_table(
        "payment_methods",
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
        sa.Column("method_type", sa.String(length=20), nullable=False),
        sa.Column("is_default", sa.Boolean, server_default=sa.text("false")),
        sa.Column("stripe_customer_id", sa.String(length=100)),
        sa.Column("stripe_payment_method_id", sa.String(length=100)),
        sa.Column("paypal_payer_id", sa.String(length=100)),
        sa.Column("card_last4", sa.String(length=4)),
        sa.Column("card_brand", sa.String(length=20)),
        sa.Column("card_exp_month", sa.Integer),
        sa.Column("card_exp_year", sa.Integer),
        sa.Column("paypal_email", sa.String(length=320)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "stripe_payment_method_id", name="uq_payment_methods_stripe"),
        sa.UniqueConstraint("tenant_id", "paypal_payer_id", name="uq_payment_methods_paypal"),
    )

    op.create_table(
        "billing_accumulated",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'EUR'")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("billing_accumulated")
    op.drop_table("payment_methods")
    op.drop_index("idx_payments_invoice", table_name="payments")
    op.drop_table("payments")
    op.drop_index("idx_invoices_due", table_name="invoices")
    op.drop_index("idx_invoices_status", table_name="invoices")
    op.drop_index("idx_invoices_tenant", table_name="invoices")
    op.drop_table("invoices")

    op.drop_column("tenants", "paypal_payer_id")
    op.drop_column("tenants", "stripe_customer_id")
    op.drop_column("tenants", "billing_status")
    op.drop_column("tenants", "billing_email")
    op.drop_column("tenants", "billing_currency")
    op.drop_column("tenants", "has_brikick_store")
    op.drop_column("tenants", "current_version")

    op.drop_index("idx_tenant_version_active", table_name="tenant_version_history")
    op.drop_index("idx_tenant_version_tenant", table_name="tenant_version_history")
    op.drop_table("tenant_version_history")

    product_version = sa.Enum("lite", "full", name="product_version")
    product_version.drop(op.get_bind(), checkfirst=True)
