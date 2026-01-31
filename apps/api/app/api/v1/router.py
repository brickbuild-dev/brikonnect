from __future__ import annotations

from fastapi import APIRouter

from app.modules.audit import router as audit_router
from app.modules.auth import router as auth_router
from app.modules.billing import router as billing_router
from app.modules.brickognize import router as brickognize_router
from app.modules.catalog import router as catalog_router
from app.modules.shipping import router as shipping_router
from app.modules.inventory import router as inventory_router
from app.modules.jobs import router as jobs_router
from app.modules.locations import router as locations_router
from app.modules.orders import router as orders_router
from app.modules.picker import router as picker_router
from app.modules.rbac import router as rbac_router
from app.modules.stores import router as stores_router
from app.modules.sync import router as sync_router
from app.modules.tenants import router as tenants_router
from app.modules.users import router as users_router
from app.modules.webhooks import router as webhooks_router
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants_router.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users_router.router, prefix="/users", tags=["users"])
api_router.include_router(rbac_router.router, prefix="/roles", tags=["rbac"])
api_router.include_router(audit_router.router, prefix="/audit", tags=["audit"])
api_router.include_router(billing_router.router)
api_router.include_router(catalog_router.router)
api_router.include_router(brickognize_router.router)
api_router.include_router(shipping_router.router)
api_router.include_router(inventory_router.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(locations_router.router, prefix="/locations", tags=["locations"])
api_router.include_router(jobs_router.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(orders_router.router, prefix="/orders", tags=["orders"])
api_router.include_router(picker_router.router, prefix="/picker", tags=["picker"])
api_router.include_router(webhooks_router.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(stores_router.router, prefix="/stores", tags=["stores"])
if settings.FEATURES.get("sync", True):
    api_router.include_router(sync_router.router, prefix="/sync", tags=["sync"])

