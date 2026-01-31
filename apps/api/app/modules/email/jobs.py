from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.email.models import EmailQueue
from app.modules.email.service import email_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def process_email_queue(db: AsyncSession, limit: int = 50) -> int:
    stmt = (
        select(EmailQueue)
        .where(EmailQueue.status == "PENDING")
        .order_by(EmailQueue.created_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    emails = list(result.scalars().all())
    processed = 0
    for email in emails:
        try:
            await email_service.send(
                to=email.to_email,
                subject=email.subject,
                body_html=email.body_html,
                body_text=email.body_text,
            )
            email.status = "SENT"
            email.sent_at = _utcnow()
        except Exception as exc:  # pragma: no cover - defensive
            email.attempts += 1
            email.last_attempt_at = _utcnow()
            email.error_message = str(exc)
            if email.attempts >= 3:
                email.status = "FAILED"
        processed += 1
    await db.flush()
    return processed
