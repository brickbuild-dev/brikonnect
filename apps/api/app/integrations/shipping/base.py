from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Address:
    name: str | None
    line1: str | None
    city: str | None
    country: str | None
    postal_code: str | None


@dataclass
class Package:
    weight_grams: int
    length_cm: int | None = None
    width_cm: int | None = None
    height_cm: int | None = None


@dataclass
class ShippingRate:
    carrier_code: str
    service_level: str
    amount: str
    currency: str
    estimated_days: int | None = None


@dataclass
class ShipmentRequest:
    order_id: str
    package: Package
    origin: Address
    destination: Address
    service_level: str


@dataclass
class LabelResponse:
    shipment_id: str
    tracking_number: str
    label_url: str
    status: str


@dataclass
class TrackingInfo:
    tracking_number: str
    status: str
    carrier_code: str
    history: list[dict] | None = None


class ShippingAdapter(Protocol):
    async def get_rates(self, package: Package, origin: Address, destination: Address) -> list[ShippingRate]:
        ...

    async def create_label(self, shipment: ShipmentRequest) -> LabelResponse:
        ...

    async def track(self, tracking_number: str) -> TrackingInfo:
        ...

    async def cancel(self, shipment_id: str) -> bool:
        ...
