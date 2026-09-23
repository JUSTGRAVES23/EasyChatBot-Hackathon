"""Unit tests for the production payment composition."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.application.composition.payment_composition import (
    PaymentComposition,
    create_payment_composition,
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
from app.application.learning.subscription_world_access_service import (
    SubscriptionWorldAccessService,
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


def _build_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PaymentComposition, object, object, object]:
    """Build the composition with a fully injected provider.

    StripePaymentProvider is patched only so the test never requires Stripe
    environment variables and never talks to Stripe.
    """
    session_factory = Mock(name="session_factory")
    world_access = Mock(
        spec=SubscriptionWorldAccessService,
        name="subscription_world_access_service",
    )
    provider = Mock(spec=StripePaymentProvider, name="stripe_provider")

    composition = create_payment_composition(
        session_factory=session_factory,
        subscription_world_access_service=world_access,
        provider=provider,
    )

    return composition, session_factory, world_access, provider


def test_create_payment_composition_builds_authoritative_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition, session_factory, world_access, provider = _build_composition(
        monkeypatch,
    )

    assert isinstance(composition, PaymentComposition)

    assert composition.provider is provider
    assert composition.subscription_world_access_service is world_access

    assert isinstance(
        composition.payment_event_repository,
        PostgreSQLPaymentEventRepository,
    )
    assert isinstance(
        composition.subscription_repository,
        PostgreSQLSubscriptionRepository,
    )
    assert isinstance(
        composition.entitlement_repository,
        PostgreSQLEntitlementRepository,
    )

    assert isinstance(
        composition.subscription_entitlement_service,
        SubscriptionEntitlementService,
    )
    assert isinstance(
        composition.world_access_orchestrator,
        SubscriptionEntitlementWorldAccessOrchestrator,
    )
    assert isinstance(
        composition.world_access_bridge,
        SubscriptionEntitlementWorldAccessBridge,
    )

    assert isinstance(
        composition.create_checkout_session,
        CreateCheckoutSession,
    )
    assert isinstance(
        composition.create_billing_portal_session,
        CreateBillingPortalSession,
    )
    assert isinstance(
        composition.process_stripe_webhook,
        ProcessStripeWebhook,
    )


def test_create_payment_composition_reuses_canonical_session_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition, session_factory, _, _ = _build_composition(monkeypatch)

    assert composition.payment_event_repository._session_factory is session_factory
    assert composition.subscription_repository._session_factory is session_factory
    assert composition.entitlement_repository._session_factory is session_factory


def test_create_payment_composition_reuses_same_provider_across_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition, _, _, provider = _build_composition(monkeypatch)

    assert composition.provider is provider
    assert composition.create_checkout_session.provider is provider
    assert composition.create_billing_portal_session.provider is provider
    assert composition.process_stripe_webhook.provider is provider


def test_create_payment_composition_wires_entitlement_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition, _, _, _ = _build_composition(monkeypatch)

    service = composition.subscription_entitlement_service

    assert (
        service.subscription_repository
        is composition.subscription_repository
    )
    assert (
        service.entitlement_repository
        is composition.entitlement_repository
    )


def test_create_payment_composition_wires_world_access_chain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition, _, world_access, _ = _build_composition(monkeypatch)

    orchestrator = composition.world_access_orchestrator
    bridge = composition.world_access_bridge

    assert (
        orchestrator._subscription_world_access_service
        is world_access
    )
    assert bridge._orchestrator is orchestrator


def test_create_payment_composition_wires_webhook_application_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    composition, _, _, provider = _build_composition(monkeypatch)

    webhook = composition.process_stripe_webhook

    assert webhook.provider is provider
    assert webhook.events is composition.payment_event_repository
    assert webhook.entitlements is composition.subscription_entitlement_service
    assert webhook.world_access_bridge is composition.world_access_bridge


def test_create_payment_composition_requires_session_factory() -> None:
    world_access = Mock(spec=SubscriptionWorldAccessService)

    with pytest.raises(ValueError, match="session_factory is required"):
        create_payment_composition(
            session_factory=None,
            subscription_world_access_service=world_access,
            provider=Mock(spec=StripePaymentProvider),
        )


def test_create_payment_composition_requires_world_access_service() -> None:
    with pytest.raises(
        ValueError,
        match="subscription_world_access_service is required",
    ):
        create_payment_composition(
            session_factory=Mock(name="session_factory"),
            subscription_world_access_service=None,
            provider=Mock(spec=StripePaymentProvider),
        )


def test_create_payment_composition_does_not_require_stripe_configuration_when_provider_is_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    composition, _, _, provider = _build_composition(monkeypatch)

    assert composition.provider is provider
