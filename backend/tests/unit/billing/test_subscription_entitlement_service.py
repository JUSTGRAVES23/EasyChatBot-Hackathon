from app.application.payment.subscription_entitlement_service import (
    SubscriptionEntitlementResult,
    SubscriptionEntitlementService,
)
from app.domain.payment.models import PaymentEvent


class FakeSubscriptionRepository:
    def __init__(self):
        self.calls = []

    def upsert(self, **kwargs):
        self.calls.append(kwargs)


class FakeEntitlementRepository:
    def __init__(self):
        self.calls = []

    def upsert(self, **kwargs):
        self.calls.append(kwargs)


def subscription_event(
    *,
    event_type="customer.subscription.created",
    status="active",
):
    return PaymentEvent(
        event_id="evt_test_subscription_001",
        event_type=event_type,
        payload={
            "id": "evt_test_subscription_001",
            "type": event_type,
            "data": {
                "object": {
                    "id": "sub_test_001",
                    "customer": "cus_test_001",
                    "status": status,
                    "cancel_at_period_end": False,
                    "current_period_start": 1758540000,
                    "current_period_end": 1761132000,
                    "metadata": {
                        "easyworld_user_id": "child-001",
                        "easyworld_payer_user_id": "parent-001",
                        "easyworld_plan_code": "PREMIUM",
                    },
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_test_premium_monthly",
                                }
                            }
                        ]
                    },
                }
            },
        },
    )


def test_active_subscription_persists_subscription_and_active_entitlement():
    subscriptions = FakeSubscriptionRepository()
    entitlements = FakeEntitlementRepository()

    service = SubscriptionEntitlementService(
        subscriptions,
        entitlements,
    )

    result = service.handle_payment_event(subscription_event())

    assert isinstance(result, SubscriptionEntitlementResult)
    assert result.beneficiary_user_id == "child-001"
    assert result.plan_code == "PREMIUM"
    assert result.active is True

    assert len(subscriptions.calls) == 1
    assert subscriptions.calls[0]["beneficiary_user_id"] == "child-001"
    assert subscriptions.calls[0]["payer_user_id"] == "parent-001"
    assert subscriptions.calls[0]["plan_code"] == "PREMIUM"
    assert subscriptions.calls[0]["status"] == "active"

    assert len(entitlements.calls) == 1
    assert entitlements.calls[0]["user_id"] == "child-001"
    assert entitlements.calls[0]["plan_code"] == "PREMIUM"
    assert entitlements.calls[0]["active"] is True


def test_past_due_subscription_does_not_grant_active_entitlement():
    subscriptions = FakeSubscriptionRepository()
    entitlements = FakeEntitlementRepository()

    service = SubscriptionEntitlementService(
        subscriptions,
        entitlements,
    )

    result = service.handle_payment_event(
        subscription_event(status="past_due")
    )

    assert isinstance(result, SubscriptionEntitlementResult)
    assert result.beneficiary_user_id == "child-001"
    assert result.plan_code == "PREMIUM"
    assert result.active is False

    assert entitlements.calls[0]["active"] is False


def test_non_subscription_event_is_ignored():
    subscriptions = FakeSubscriptionRepository()
    entitlements = FakeEntitlementRepository()

    service = SubscriptionEntitlementService(
        subscriptions,
        entitlements,
    )

    result = service.handle_payment_event(
        PaymentEvent(
            event_id="evt_payment",
            event_type="payment_intent.succeeded",
            payload={},
        )
    )

    assert result is None
    assert subscriptions.calls == []
    assert entitlements.calls == []


def test_subscription_entitlement_result_is_immutable():
    result = SubscriptionEntitlementResult(
        beneficiary_user_id="child-001",
        plan_code="PREMIUM",
        active=True,
    )

    try:
        result.active = False
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "SubscriptionEntitlementResult must be immutable."
        )