from __future__ import annotations

import uuid

from app.integrations.shipping.base import Address, LabelResponse, Package, ShippingRate, TrackingInfo, ShipmentRequest


class PirateShipAdapter:
    carrier_code = "pirateship"

    async def get_rates(self, package: Package, origin: Address, destination: Address) -> list[ShippingRate]:
        base = 3.75 + (package.weight_grams / 1000) * 1.1
        return [
            ShippingRate(
                carrier_code=self.carrier_code,
                service_level="ground",
                amount=f"{base:.2f}",
                currency="USD",
                estimated_days=5,
            )
        ]

    async def create_label(self, shipment: ShipmentRequest) -> LabelResponse:
        shipment_id = f"ps_{uuid.uuid4().hex}"
        tracking = f"PS{uuid.uuid4().hex[:10].upper()}"
        label_url = f"https://labels.pirateship.fake/{shipment_id}.pdf"
        return LabelResponse(
            shipment_id=shipment_id,
            tracking_number=tracking,
            label_url=label_url,
            status="CREATED",
        )

    async def track(self, tracking_number: str) -> TrackingInfo:
        return TrackingInfo(
            tracking_number=tracking_number,
            status="IN_TRANSIT",
            carrier_code=self.carrier_code,
            history=[{"status": "IN_TRANSIT"}],
        )

    async def cancel(self, shipment_id: str) -> bool:
        return True
