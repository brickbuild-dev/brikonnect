from __future__ import annotations

from fastapi import Depends, Request

from app.modules.audit.service import AuditContext
from app.modules.auth.deps import get_current_user


async def get_audit_context(request: Request, user=Depends(get_current_user)) -> AuditContext:
    return AuditContext(
        tenant_id=user.tenant_id,
        actor_type="USER",
        actor_id=user.id,
        actor_name=user.email,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
