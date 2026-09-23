from app.application.payment.payment_event_router import PaymentEventRouter
from app.domain.payment.models import PaymentEvent


class FakeSubscriptionEntitlementService:
    def __init__(self):
        self.events = []

    def handle_payment_event(self, event):
        self.events.append(event)


def test_payment_event_router_delegates_verified_event():
    handler = FakeSubscriptionEntitlementService()
    router = PaymentEventRouter(handler)

    event = PaymentEvent(
        event_id="evt_router_001",
        event_type="customer.subscription.updated",
        payload={"data": {"object": {}}},
    )

    router.handle_payment_event(event)

    assert handler.events == [event]


def test_payment_event_router_rejects_invalid_event():
    handler = FakeSubscriptionEntitlementService()
    router = PaymentEventRouter(handler)

    try:
        router.handle_payment_event(object())
    except TypeError:
        pass
    else:
        raise AssertionError("Expected TypeError")
