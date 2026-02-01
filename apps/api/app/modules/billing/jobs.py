from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.service import check_overdue_invoices, generate_monthly_invoices, send_invoice_reminders


async def generate_monthly_invoices_job(db: AsyncSession) -> int:
    invoices = await generate_monthly_invoices(db)
    return len(invoices)


async def check_overdue_invoices_job(db: AsyncSession) -> int:
    tenants = await check_overdue_invoices(db)
    return len(tenants)


async def send_invoice_reminders_job(db: AsyncSession) -> int:
    return await send_invoice_reminders(db)
