from __future__ import annotations

import uuid
from decimal import Decimal


async def create_paypal_order(
    amount: Decimal,
    currency: str,
    payer_id: str | None = None,
) -> dict:
    return {
        "id": f"order_{uuid.uuid4().hex}",
        "amount": str(amount),
        "currency": currency,
        "payer_id": payer_id,
        "status": "CREATED",
    }
