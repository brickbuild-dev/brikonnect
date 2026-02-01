from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.email.models import EmailQueue, EmailTemplate

SYSTEM_TEMPLATES = {
    "welcome": {
        "subject": "Welcome to Brikonnect!",
        "variables": ["user_name", "tenant_name", "login_url"],
        "body_html": "<p>Welcome {user_name}!</p>",
        "body_text": "Welcome {user_name}!",
    },
    "password_reset": {
        "subject": "Reset your password",
        "variables": ["user_name", "reset_url", "expires_in"],
        "body_html": "<p>Hello {user_name}, reset here: {reset_url}</p>",
        "body_text": "Hello {user_name}, reset here: {reset_url}",
    },
    "order_shipped": {
        "subject": "Your order has shipped - {order_no}",
        "variables": ["buyer_name", "order_no", "tracking_number", "tracking_url"],
        "body_html": "<p>Your order {order_no} shipped.</p>",
        "body_text": "Your order {order_no} shipped.",
    },
    "invoice_issued": {
        "subject": "Your Brikonnect invoice for {month}",
        "variables": ["tenant_name", "month", "amount", "due_date", "pay_url"],
        "body_html": "<p>Invoice for {month}: {amount}</p>",
        "body_text": "Invoice for {month}: {amount}",
    },
    "invoice_overdue": {
        "subject": "Payment overdue - Action required",
        "variables": ["tenant_name", "amount", "pay_url"],
        "body_html": "<p>Payment overdue: {amount}</p>",
        "body_text": "Payment overdue: {amount}",
    },
    "sync_completed": {
        "subject": "Sync completed successfully",
        "variables": ["sync_type", "items_updated", "items_added", "items_removed"],
        "body_html": "<p>Sync completed for {sync_type}.</p>",
        "body_text": "Sync completed for {sync_type}.",
    },
    "sync_failed": {
        "subject": "Sync failed - Action required",
        "variables": ["sync_type", "error_message"],
        "body_html": "<p>Sync failed: {error_message}</p>",
        "body_text": "Sync failed: {error_message}",
    },
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _safe_format(template: str, variables: dict | None) -> str:
    if not variables:
        return template
    try:
        return template.format(**variables)
    except KeyError:
        return template


async def _get_template(
    db: AsyncSession,
    template_key: str,
    tenant_id: UUID | None,
) -> dict | None:
    stmt = select(EmailTemplate).where(EmailTemplate.template_key == template_key)
    if tenant_id:
        stmt = stmt.where(EmailTemplate.tenant_id == tenant_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if template and template.is_active:
        return {
            "subject": template.subject,
            "body_html": template.body_html,
            "body_text": template.body_text,
        }
    return SYSTEM_TEMPLATES.get(template_key)


class EmailService:
    async def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
    ) -> bool:
        return True

    async def send_template(
        self,
        db: AsyncSession,
        to: str,
        template_key: str,
        variables: dict,
        tenant_id: UUID | None = None,
    ) -> bool:
        template = await _get_template(db, template_key, tenant_id)
        if not template:
            raise ValueError("Template not found")
        subject = _safe_format(template["subject"], variables)
        body_html = _safe_format(template["body_html"], variables)
        body_text = _safe_format(template.get("body_text") or "", variables)
        return await self.send(to=to, subject=subject, body_html=body_html, body_text=body_text)

    async def queue_email(
        self,
        db: AsyncSession,
        to: str,
        template_key: str,
        variables: dict,
        tenant_id: UUID | None = None,
        to_name: str | None = None,
    ) -> UUID:
        template = await _get_template(db, template_key, tenant_id)
        if not template:
            raise ValueError("Template not found")
        subject = _safe_format(template["subject"], variables)
        body_html = _safe_format(template["body_html"], variables)
        body_text = _safe_format(template.get("body_text") or "", variables)
        email = EmailQueue(
            tenant_id=tenant_id,
            to_email=to,
            to_name=to_name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            status="PENDING",
            attempts=0,
            template_key=template_key,
            created_at=_utcnow(),
        )
        db.add(email)
        await db.flush()
        return email.id


email_service = EmailService()
