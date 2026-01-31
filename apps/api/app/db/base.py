from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

# Import models for Alembic autogeneration
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.inventory import models as inventory_models  # noqa: F401
from app.modules.jobs import models as job_models  # noqa: F401
from app.modules.locations import models as location_models  # noqa: F401
from app.modules.rbac import models as rbac_models  # noqa: F401
from app.modules.tenants import models as tenant_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401

class Base(DeclarativeBase):
    pass
