from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth import router as auth_router
from app.modules.inventory import router as inventory_router
from app.modules.jobs import router as jobs_router
from app.modules.locations import router as locations_router
from app.modules.orders import router as orders_router
from app.modules.rbac import router as rbac_router
from app.modules.tenants import router as tenants_router
from app.modules.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants_router.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users_router.router, prefix="/users", tags=["users"])
api_router.include_router(rbac_router.router, prefix="/roles", tags=["rbac"])
api_router.include_router(inventory_router.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(locations_router.router, prefix="/locations", tags=["locations"])
api_router.include_router(jobs_router.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(orders_router.router, prefix="/orders", tags=["orders"])

