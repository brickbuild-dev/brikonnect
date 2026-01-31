from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models for Alembic autogeneration
from app.modules.audit import models as audit_models  # noqa: E402,F401
from app.modules.auth import models as auth_models  # noqa: E402,F401
from app.modules.billing import models as billing_models  # noqa: E402,F401
from app.modules.catalog import models as catalog_models  # noqa: E402,F401
from app.modules.events import models as event_models  # noqa: E402,F401
from app.modules.inventory import models as inventory_models  # noqa: E402,F401
from app.modules.jobs import models as job_models  # noqa: E402,F401
from app.modules.locations import models as location_models  # noqa: E402,F401
from app.modules.orders import models as order_models  # noqa: E402,F401
from app.modules.picker import models as picker_models  # noqa: E402,F401
from app.modules.rbac import models as rbac_models  # noqa: E402,F401
from app.modules.stores import models as store_models  # noqa: E402,F401
from app.modules.sync import models as sync_models  # noqa: E402,F401
from app.modules.tenants import models as tenant_models  # noqa: E402,F401
from app.modules.users import models as user_models  # noqa: E402,F401
from app.modules.webhooks import models as webhook_models  # noqa: E402,F401
