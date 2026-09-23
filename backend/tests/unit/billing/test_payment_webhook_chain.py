from app.application.payment.services import ProcessStripeWebhook
from app.application.payment.subscription_entitlement_service import (
    SubscriptionEntitlementService,
)
from app.domain.payment.models import PaymentEvent
from app.infrastructure.payment.in_memory_repositories import (
    InMemoryPaymentEventRepository,
)


class FakePaymentProvider:
    def __init__(self, event):
        self.event = event

    def construct_webhook_event(self, payload, signature):
        return self.event


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


def test_webhook_processing_is_idempotent_before_entitlement_application():
    event = PaymentEvent(
        event_id="evt_chain_001",
        event_type="customer.subscription.created",
        payload={
            "data": {
                "object": {
                    "id": "sub_chain_001",
                    "customer": "cus_chain_001",
                    "status": "active",
                    "cancel_at_period_end": False,
                    "metadata": {
                        "easyworld_user_id": "child-chain",
                        "easyworld_payer_user_id": "parent-chain",
                        "easyworld_plan_code": "PREMIUM",
                    },
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_chain_001",
                                }
                            }
                        ]
                    },
                }
            }
        },
    )

    provider = FakePaymentProvider(event)
    events = InMemoryPaymentEventRepository()

    subscriptions = FakeSubscriptionRepository()
    entitlements = FakeEntitlementRepository()

    handler = SubscriptionEntitlementService(
        subscriptions,
        entitlements,
    )

    processor = ProcessStripeWebhook(
        provider,
        events,
        handler,
    )

    first = processor.execute(
        payload=b"payload",
        signature="signature",
    )

    second = processor.execute(
        payload=b"payload",
        signature="signature",
    )

    assert first["status"] == "processed"
    assert second["status"] == "already_processed"

    assert len(subscriptions.calls) == 1
    assert len(entitlements.calls) == 1

    assert entitlements.calls[0]["user_id"] == "child-chain"
    assert entitlements.calls[0]["active"] is True
