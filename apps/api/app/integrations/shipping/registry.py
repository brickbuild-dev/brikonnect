from __future__ import annotations

from app.integrations.shipping.dhl import DHLAdapter
from app.integrations.shipping.pirateship import PirateShipAdapter
from app.integrations.shipping.postnl import PostNLAdapter
from app.integrations.shipping.sendcloud import SendCloudAdapter
from app.integrations.shipping.shipstation import ShipStationAdapter

ADAPTERS = {
    "sendcloud": SendCloudAdapter(),
    "shipstation": ShipStationAdapter(),
    "pirateship": PirateShipAdapter(),
    "dhl": DHLAdapter(),
    "postnl": PostNLAdapter(),
}


def get_adapter(carrier_code: str):
    adapter = ADAPTERS.get(carrier_code)
    if not adapter:
        raise ValueError(f"Unsupported carrier: {carrier_code}")
    return adapter
