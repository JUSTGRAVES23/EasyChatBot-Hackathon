from __future__ import annotations

import os
from typing import Any

import stripe

from app.application.payment.ports import PaymentProvider
from app.domain.payment.models import BillingPortalSession, CheckoutRequest, CheckoutSession, PaymentEvent


class StripePaymentProvider(PaymentProvider):
    """Stripe infrastructure adapter. Keep Stripe-specific SDK usage here."""

    def __init__(self, secret_key: str | None = None, webhook_secret: str | None = None):
        self.secret_key = secret_key or os.environ["STRIPE_SECRET_KEY"]
        self.webhook_secret = webhook_secret or os.environ["STRIPE_WEBHOOK_SECRET"]
        stripe.api_key = self.secret_key

    def create_customer(self, *, user_id: str, email: str, name: str | None = None) -> str:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"easyworld_user_id": user_id},
        )
        return customer.id

    def create_checkout_session(self, request: CheckoutRequest, *, customer_id: str | None) -> CheckoutSession:
        params: dict[str, Any] = {
            "mode": request.mode.value,
            "line_items": [{"price": request.price_id, "quantity": 1}],
            "success_url": request.success_url,
            "cancel_url": request.cancel_url,
            "metadata": {
                "easyworld_user_id": request.user_id,
                "easyworld_price_id": request.price_id,
            },
        }
        if customer_id:
            params["customer"] = customer_id

        session = stripe.checkout.Session.create(**params)
        return CheckoutSession(
            provider_session_id=session.id,
            checkout_url=session.url,
        )

    def create_billing_portal_session(self, *, customer_id: str, return_url: str) -> BillingPortalSession:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return BillingPortalSession(
            provider_session_id=session.id,
            portal_url=session.url,
        )

    def construct_webhook_event(self, payload: bytes, signature: str) -> PaymentEvent:
        event = stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
        return PaymentEvent(
            event_id=event["id"],
            event_type=event["type"],
            payload=event.to_dict_recursive(),
        )
