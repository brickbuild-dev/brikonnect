import pytest

from app.modules.email.jobs import process_email_queue
from app.modules.email.models import EmailQueue
from app.modules.email.service import email_service
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant


@pytest.mark.asyncio
async def test_queue_email(db_session):
    tenant = await create_tenant(db_session, TenantCreate(slug="email", name="Email"))
    email_id = await email_service.queue_email(
        db_session,
        to="user@example.com",
        template_key="welcome",
        variables={"user_name": "User", "tenant_name": "Email", "login_url": "https://example.com"},
        tenant_id=tenant.id,
    )
    await db_session.commit()
    email = await db_session.get(EmailQueue, email_id)
    assert email is not None
    assert email.status == "PENDING"


@pytest.mark.asyncio
async def test_process_email_queue(db_session):
    await email_service.queue_email(
        db_session,
        to="user@example.com",
        template_key="welcome",
        variables={"user_name": "User", "tenant_name": "Email", "login_url": "https://example.com"},
        tenant_id=None,
    )
    await db_session.commit()

    processed = await process_email_queue(db_session, limit=10)
    await db_session.commit()
    assert processed == 1
