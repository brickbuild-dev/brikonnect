from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.rbac.deps import require_permissions
from app.modules.shipping.schemas import (
    CreateLabelRequest,
    ShipmentOut,
    ShippingCarrierConfigCreate,
    ShippingCarrierConfigOut,
    ShippingRateOut,
    ShippingRatesRequest,
    TrackingOut,
)
from app.modules.shipping.service import (
    cancel_shipment,
    create_label,
    get_rates,
    get_shipment,
    list_carriers,
    track_shipment,
    upsert_carrier,
)

router = APIRouter(prefix="/shipping", tags=["shipping"])


@router.get("/carriers", response_model=list[ShippingCarrierConfigOut])
async def carriers(
    current_user=Depends(require_permissions(["shipping:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await list_carriers(db, current_user.tenant_id)


@router.post("/carriers", response_model=ShippingCarrierConfigOut, status_code=201)
async def add_carrier(
    payload: ShippingCarrierConfigCreate,
    current_user=Depends(require_permissions(["shipping:manage"])),
    db: AsyncSession = Depends(get_db),
):
    config = await upsert_carrier(
        db,
        current_user.tenant_id,
        payload.carrier_code,
        payload.credentials,
        payload.is_enabled,
    )
    await db.commit()
    return config


@router.post("/rates", response_model=list[ShippingRateOut])
async def rates(
    payload: ShippingRatesRequest,
    current_user=Depends(require_permissions(["shipping:read"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_rates(db, current_user.tenant_id, payload.order_id, payload.carrier_codes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/labels", response_model=ShipmentOut, status_code=201)
async def create_label_endpoint(
    payload: CreateLabelRequest,
    current_user=Depends(require_permissions(["shipping:manage"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        shipment = await create_label(
            db,
            current_user.tenant_id,
            payload.order_id,
            payload.carrier_code,
            payload.service_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await db.commit()
    return shipment


@router.get("/labels/{shipment_id}", response_model=ShipmentOut)
async def get_label(
    shipment_id: UUID,
    current_user=Depends(require_permissions(["shipping:read"])),
    db: AsyncSession = Depends(get_db),
):
    shipment = await get_shipment(db, current_user.tenant_id, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@router.get("/track/{tracking_number}", response_model=TrackingOut)
async def track(
    tracking_number: str,
    carrier_code: str,
    current_user=Depends(require_permissions(["shipping:read"])),
    db: AsyncSession = Depends(get_db),
):
    return await track_shipment(db, carrier_code, tracking_number)


@router.post("/labels/{shipment_id}/cancel", response_model=ShipmentOut)
async def cancel(
    shipment_id: UUID,
    current_user=Depends(require_permissions(["shipping:manage"])),
    db: AsyncSession = Depends(get_db),
):
    shipment = await get_shipment(db, current_user.tenant_id, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    shipment = await cancel_shipment(db, shipment)
    await db.commit()
    return shipment
