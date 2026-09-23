from __future__ import annotations

from app.application.payment.ports import EntitlementService
from app.domain.payment.models import PaymentEvent


class PaymentEventRouter(EntitlementService):
    """Route verified payment events to the appropriate application handler.

    This class does not:
    - verify Stripe signatures;
    - call the Stripe SDK;
    - persist webhook events;
    - decide whether Checkout succeeded.

    Those responsibilities remain in their existing layers.
    """

    def __init__(
        self,
        subscription_entitlement_service,
    ) -> None:
        if subscription_entitlement_service is None:
            raise ValueError(
                "subscription_entitlement_service cannot be None."
            )

        self.subscription_entitlement_service = (
            subscription_entitlement_service
        )

    def handle_payment_event(self, event: PaymentEvent) -> None:
        if not isinstance(event, PaymentEvent):
            raise TypeError("event must be a PaymentEvent.")

        self.subscription_entitlement_service.handle_payment_event(event)


__all__ = ["PaymentEventRouter"]
