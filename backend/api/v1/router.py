from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, tenants, inventory, orders, picker, billing, notifications, definitions
from app.api.v1.compat.brikonnect import router as brikonnect_compat_router

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(picker.router, prefix="/picker", tags=["picker"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(definitions.router, prefix="/definitions", tags=["definitions"])

# Compatibility endpoints (optional)
api_router.include_router(brikonnect_compat_router, tags=["compat"])
