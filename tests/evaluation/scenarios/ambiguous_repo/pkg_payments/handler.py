"""Payment processing handler package."""

class Handler:
    """Handles credit card and checkout transaction requests."""
    def handle(self, request: dict) -> dict:
        return {"action": "payment_charge", "amount": request.get("amount")}

