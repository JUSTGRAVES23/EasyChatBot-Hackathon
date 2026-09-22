from __future__ import annotations

from app.application.payment.ports import EntitlementService, PaymentEventRepository, PaymentProvider
from app.domain.payment.models import CheckoutRequest


class CreateCheckoutSession:
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def execute(self, request: CheckoutRequest, *, stripe_customer_id: str | None):
        return self.provider.create_checkout_session(request, customer_id=stripe_customer_id)


class CreateBillingPortalSession:
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def execute(self, *, stripe_customer_id: str, return_url: str):
        return self.provider.create_billing_portal_session(
            customer_id=stripe_customer_id,
            return_url=return_url,
        )


class ProcessStripeWebhook:
    def __init__(self, provider: PaymentProvider, events: PaymentEventRepository, entitlements: EntitlementService):
        self.provider = provider
        self.events = events
        self.entitlements = entitlements

    def execute(self, *, payload: bytes, signature: str):
        event = self.provider.construct_webhook_event(payload, signature)
        if self.events.has_processed(event.event_id):
            return {"status": "already_processed", "event_id": event.event_id}

        self.events.record_received(event)
        try:
            self.entitlements.handle_payment_event(event)
            self.events.mark_processed(event.event_id)
            return {"status": "processed", "event_id": event.event_id}
        except Exception as exc:
            self.events.mark_failed(event.event_id, str(exc))
            raise
