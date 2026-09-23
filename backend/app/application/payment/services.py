from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.payment.ports import (
    EntitlementService,
    PaymentEventRepository,
    PaymentProvider,
)
from app.domain.payment.models import CheckoutRequest

if TYPE_CHECKING:
    from app.application.payment.subscription_entitlement_world_access_bridge import (
        SubscriptionEntitlementWorldAccessBridge,
    )


class CreateCheckoutSession:
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def execute(
        self,
        request: CheckoutRequest,
        *,
        stripe_customer_id: str | None,
    ):
        return self.provider.create_checkout_session(
            request,
            customer_id=stripe_customer_id,
        )


class CreateBillingPortalSession:
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def execute(
        self,
        *,
        stripe_customer_id: str,
        return_url: str,
    ):
        return self.provider.create_billing_portal_session(
            customer_id=stripe_customer_id,
            return_url=return_url,
        )


class ProcessStripeWebhook:
    def __init__(
        self,
        provider: PaymentProvider,
        events: PaymentEventRepository,
        entitlements: EntitlementService,
        world_access_bridge: SubscriptionEntitlementWorldAccessBridge | None = None,
    ):
        self.provider = provider
        self.events = events
        self.entitlements = entitlements
        self.world_access_bridge = world_access_bridge

    def execute(
        self,
        *,
        payload: bytes,
        signature: str,
    ):
        """
        Process a Stripe webhook using the existing synchronous contract.

        This method is intentionally preserved for backward compatibility
        with the existing payment foundation and tests.

        It does not invoke the asynchronous World-access boundary.
        Production webhook execution that requires World-access reconciliation
        must use ``execute_async()``.
        """
        event = self.provider.construct_webhook_event(
            payload,
            signature,
        )

        if self.events.has_processed(event.event_id):
            return {
                "status": "already_processed",
                "event_id": event.event_id,
            }

        self.events.record_received(event)

        try:
            self.entitlements.handle_payment_event(event)
            self.events.mark_processed(event.event_id)

            return {
                "status": "processed",
                "event_id": event.event_id,
            }

        except Exception as exc:
            self.events.mark_failed(
                event.event_id,
                str(exc),
            )
            raise

    async def execute_async(
        self,
        *,
        payload: bytes,
        signature: str,
    ):
        """
        Process a Stripe webhook through the production async boundary.

        Processing order is deliberately:

            verify Stripe event
                -> durable idempotency check
                -> record received
                -> persist entitlement state
                -> reconcile World access
                -> mark processed

        ``mark_processed`` is therefore only reached after World-access
        reconciliation succeeds.

        No background task, scheduler, ``asyncio.run()``, or fire-and-forget
        execution is used here. The caller owns the request lifecycle and
        awaits this method to completion.
        """
        if self.world_access_bridge is None:
            raise RuntimeError(
                "world_access_bridge is required for asynchronous "
                "Stripe webhook processing."
            )

        event = self.provider.construct_webhook_event(
            payload,
            signature,
        )

        if self.events.has_processed(event.event_id):
            return {
                "status": "already_processed",
                "event_id": event.event_id,
            }

        self.events.record_received(event)

        try:
            result = self.entitlements.handle_payment_event(event)

            if result is not None:
                await self.world_access_bridge.synchronize(result)

            self.events.mark_processed(event.event_id)

            return {
                "status": "processed",
                "event_id": event.event_id,
            }

        except Exception as exc:
            self.events.mark_failed(
                event.event_id,
                str(exc),
            )
            raise