import pytest

from app.modules.notifications.models import Notification
from app.modules.notifications.service import dismiss, list_notifications, mark_read
from app.modules.tenants.schemas import TenantCreate
from app.modules.tenants.service import create_tenant
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user


@pytest.mark.asyncio
async def test_notifications_flow(db_session):
    tenant = await create_tenant(db_session, TenantCreate(slug="notify", name="Notify"))
    user = await create_user(
        db_session,
        tenant.id,
        UserCreate(email="user@example.com", password="password123"),
        "hashed:password123",
    )
    notification = Notification(
        tenant_id=tenant.id,
        user_id=user.id,
        type="info",
        title="Test",
        body="Test notification",
    )
    db_session.add(notification)
    await db_session.commit()

    notifications = await list_notifications(db_session, tenant.id, user.id)
    assert len(notifications) == 1

    notification = await mark_read(db_session, notifications[0])
    await db_session.commit()
    assert notification.read_at is not None

    notification = await dismiss(db_session, notification)
    await db_session.commit()
    assert notification.dismissed_at is not None
