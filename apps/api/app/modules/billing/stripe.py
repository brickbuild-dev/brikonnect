from __future__ import annotations

import uuid
from decimal import Decimal


async def create_payment_intent(
    amount: Decimal,
    currency: str,
    customer_id: str | None = None,
    payment_method_id: str | None = None,
) -> dict:
    return {
        "id": f"pi_{uuid.uuid4().hex}",
        "amount": str(amount),
        "currency": currency,
        "customer_id": customer_id,
        "payment_method_id": payment_method_id,
        "status": "succeeded",
    }
