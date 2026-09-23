"""Production composition for EASYWORLD payment and entitlement services.

This module composes the existing payment provider/repository adapters with the
existing subscription entitlement and World-access application boundaries.

The composition deliberately reuses the caller-owned canonical SQLAlchemy
session_factory and caller-owned subscription World-access service. It does not
create a second database graph, WorldAccessService, route, scheduler, or task.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.learning.subscription_world_access_service import (
    SubscriptionWorldAccessService,
)
from app.application.payment.services import (
    CreateBillingPortalSession,
    CreateCheckoutSession,
    ProcessStripeWebhook,
)
from app.application.payment.subscription_entitlement_service import (
    SubscriptionEntitlementService,
)
from app.application.payment.subscription_entitlement_world_access_bridge import (
    SubscriptionEntitlementWorldAccessBridge,
)
from app.application.payment.subscription_entitlement_world_access_orchestrator import (
    SubscriptionEntitlementWorldAccessOrchestrator,
)
from app.infrastructure.payment.stripe_provider import StripePaymentProvider
from app.infrastructure.persistence.postgresql_entitlement_repository import (
    PostgreSQLEntitlementRepository,
)
from app.infrastructure.persistence.postgresql_payment_event_repository import (
    PostgreSQLPaymentEventRepository,
)
from app.infrastructure.persistence.postgresql_subscription_repository import (
    PostgreSQLSubscriptionRepository,
)


@dataclass(frozen=True, slots=True)
class PaymentComposition:
    """Authoritative production payment composition."""

    provider: StripePaymentProvider
    payment_event_repository: PostgreSQLPaymentEventRepository
    subscription_repository: PostgreSQLSubscriptionRepository
    entitlement_repository: PostgreSQLEntitlementRepository
    subscription_entitlement_service: SubscriptionEntitlementService
    subscription_world_access_service: SubscriptionWorldAccessService
    world_access_orchestrator: SubscriptionEntitlementWorldAccessOrchestrator
    world_access_bridge: SubscriptionEntitlementWorldAccessBridge
    create_checkout_session: CreateCheckoutSession
    create_billing_portal_session: CreateBillingPortalSession
    process_stripe_webhook: ProcessStripeWebhook


def create_payment_composition(
    *,
    session_factory: Any,
    subscription_world_access_service: SubscriptionWorldAccessService,
    provider: StripePaymentProvider | None = None,
) -> PaymentComposition:
    """Create the production payment application graph.

    ``session_factory`` is the canonical synchronous SQLAlchemy factory owned
    by the application's composition root.

    ``subscription_world_access_service`` is injected rather than rebuilt here
    so the existing WorldAccessService and entitlement policy remain the sole
    authorization graph.

    ``provider`` is injectable for isolated composition tests; production uses
    StripePaymentProvider, which reads the configured Stripe secrets.
    """
    if session_factory is None:
        raise ValueError("session_factory is required.")

    if subscription_world_access_service is None:
        raise ValueError("subscription_world_access_service is required.")

    payment_provider = provider or StripePaymentProvider()

    payment_event_repository = PostgreSQLPaymentEventRepository(
        session_factory=session_factory,
    )
    subscription_repository = PostgreSQLSubscriptionRepository(
        session_factory=session_factory,
    )
    entitlement_repository = PostgreSQLEntitlementRepository(
        session_factory=session_factory,
    )

    subscription_entitlement_service = SubscriptionEntitlementService(
        subscription_repository=subscription_repository,
        entitlement_repository=entitlement_repository,
    )

    world_access_orchestrator = SubscriptionEntitlementWorldAccessOrchestrator(
        subscription_world_access_service=subscription_world_access_service,
    )
    world_access_bridge = SubscriptionEntitlementWorldAccessBridge(
        world_access_orchestrator,
    )

    create_checkout_session = CreateCheckoutSession(payment_provider)
    create_billing_portal_session = CreateBillingPortalSession(payment_provider)

    process_stripe_webhook = ProcessStripeWebhook(
        provider=payment_provider,
        events=payment_event_repository,
        entitlements=subscription_entitlement_service,
        world_access_bridge=world_access_bridge,
    )

    return PaymentComposition(
        provider=payment_provider,
        payment_event_repository=payment_event_repository,
        subscription_repository=subscription_repository,
        entitlement_repository=entitlement_repository,
        subscription_entitlement_service=subscription_entitlement_service,
        subscription_world_access_service=subscription_world_access_service,
        world_access_orchestrator=world_access_orchestrator,
        world_access_bridge=world_access_bridge,
        create_checkout_session=create_checkout_session,
        create_billing_portal_session=create_billing_portal_session,
        process_stripe_webhook=process_stripe_webhook,
    )


__all__ = [
    "PaymentComposition",
    "create_payment_composition",
]
