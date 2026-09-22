"""Framework-neutral route blueprint.

Adapt these handlers to the canonical EASYWORLD FastAPI router instead of creating a second API stack.
"""

from app.application.payment.services import CreateBillingPortalSession, CreateCheckoutSession, ProcessStripeWebhook
from app.domain.payment.models import CheckoutMode, CheckoutRequest


def create_checkout(*, service: CreateCheckoutSession, user_id: str, stripe_customer_id: str | None, price_id: str, success_url: str, cancel_url: str, mode: str):
    request = CheckoutRequest(
        user_id=user_id,
        price_id=price_id,
        mode=CheckoutMode(mode),
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return service.execute(request, stripe_customer_id=stripe_customer_id)


def create_portal(*, service: CreateBillingPortalSession, stripe_customer_id: str, return_url: str):
    return service.execute(stripe_customer_id=stripe_customer_id, return_url=return_url)


def stripe_webhook(*, service: ProcessStripeWebhook, payload: bytes, signature: str):
    return service.execute(payload=payload, signature=signature)
