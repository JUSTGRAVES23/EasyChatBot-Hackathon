from __future__ import annotations

from app.domain.payment.models import PaymentEvent


class NoOpEntitlementService:
    """Safe P1–P4 placeholder while EASYWORLD remains free.

    Webhooks can be verified and recorded in tests without granting paid access.
    Replace with the real EASYWORLD entitlement service in the paid-readiness milestone.
    """

    def handle_payment_event(self, event: PaymentEvent) -> None:
        return None
