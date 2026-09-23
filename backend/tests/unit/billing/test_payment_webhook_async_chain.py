from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.payment.services import ProcessStripeWebhook
from app.application.payment.subscription_entitlement_service import (
    SubscriptionEntitlementResult,
)
from app.domain.payment.models import PaymentEvent
from app.infrastructure.payment.in_memory_repositories import (
    InMemoryPaymentEventRepository,
)


class FakePaymentProvider:
    def __init__(self, event: PaymentEvent):
        self.event = event

    def construct_webhook_event(
        self,
        payload: bytes,
        signature: str,
    ) -> PaymentEvent:
        return self.event


class FakeEntitlementService:
    def __init__(
        self,
        result: SubscriptionEntitlementResult | None,
    ):
        self.result = result
        self.calls: list[PaymentEvent] = []

    def handle_payment_event(
        self,
        event: PaymentEvent,
    ) -> SubscriptionEntitlementResult | None:
        self.calls.append(event)
        return self.result


class FakeWorldAccessBridge:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls: list[SubscriptionEntitlementResult] = []

    async def synchronize(
        self,
        result: SubscriptionEntitlementResult,
    ) -> None:
        self.calls.append(result)

        if self.error is not None:
            raise self.error


class RecordingPaymentEventRepository(InMemoryPaymentEventRepository):
    def __init__(self):
        super().__init__()
        self.mark_processed_calls: list[str] = []
        self.mark_failed_calls: list[tuple[str, str]] = []

    def mark_processed(self, event_id: str) -> None:
        self.mark_processed_calls.append(event_id)
        super().mark_processed(event_id)

    def mark_failed(self, event_id: str, error: str) -> None:
        self.mark_failed_calls.append((event_id, error))
        super().mark_failed(event_id, error)


def _subscription_event() -> PaymentEvent:
    user_id = str(uuid4())

    return PaymentEvent(
        event_id="evt_async_subscription_001",
        event_type="customer.subscription.updated",
        payload={
            "data": {
                "object": {
                    "id": "sub_async_001",
                    "customer": "cus_async_001",
                    "status": "active",
                    "cancel_at_period_end": False,
                    "metadata": {
                        "easyworld_user_id": user_id,
                        "easyworld_payer_user_id": user_id,
                        "easyworld_plan_code": "PREMIUM",
                    },
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_async_001",
                                },
                            },
                        ],
                    },
                },
            },
        },
    )


def test_async_subscription_event_reaches_world_access_before_processed():
    event = _subscription_event()

    entitlement_result = SubscriptionEntitlementResult(
        beneficiary_user_id=event.payload["data"]["object"]["metadata"][
            "easyworld_user_id"
        ],
        plan_code="PREMIUM",
        active=True,
    )

    provider = FakePaymentProvider(event)
    events = RecordingPaymentEventRepository()
    entitlements = FakeEntitlementService(entitlement_result)
    bridge = FakeWorldAccessBridge()

    processor = ProcessStripeWebhook(
        provider,
        events,
        entitlements,
        bridge,
    )

    result = pytest.run(async_test=True)


@pytest.mark.asyncio
async def test_async_subscription_event_reaches_world_access_before_processed():
    event = _subscription_event()

    entitlement_result = SubscriptionEntitlementResult(
        beneficiary_user_id=event.payload["data"]["object"]["metadata"][
            "easyworld_user_id"
        ],
        plan_code="PREMIUM",
        active=True,
    )

    provider = FakePaymentProvider(event)
    events = RecordingPaymentEventRepository()
    entitlements = FakeEntitlementService(entitlement_result)
    bridge = FakeWorldAccessBridge()

    processor = ProcessStripeWebhook(
        provider,
        events,
        entitlements,
        bridge,
    )

    result = await processor.execute_async(
        payload=b"payload",
        signature="signature",
    )

    assert result == {
        "status": "processed",
        "event_id": event.event_id,
    }

    assert entitlements.calls == [event]
    assert bridge.calls == [entitlement_result]
    assert events.mark_processed_calls == [event.event_id]
    assert events.mark_failed_calls == []


@pytest.mark.asyncio
async def test_async_non_subscription_event_does_not_call_world_access():
    event = PaymentEvent(
        event_id="evt_async_non_subscription_001",
        event_type="invoice.payment_failed",
        payload={"data": {"object": {}}},
    )

    provider = FakePaymentProvider(event)
    events = RecordingPaymentEventRepository()
    entitlements = FakeEntitlementService(None)
    bridge = FakeWorldAccessBridge()

    processor = ProcessStripeWebhook(
        provider,
        events,
        entitlements,
        bridge,
    )

    result = await processor.execute_async(
        payload=b"payload",
        signature="signature",
    )

    assert result == {
        "status": "processed",
        "event_id": event.event_id,
    }

    assert entitlements.calls == [event]
    assert bridge.calls == []
    assert events.mark_processed_calls == [event.event_id]
    assert events.mark_failed_calls == []


@pytest.mark.asyncio
async def test_async_world_access_failure_keeps_webhook_retryable():
    event = _subscription_event()

    entitlement_result = SubscriptionEntitlementResult(
        beneficiary_user_id=event.payload["data"]["object"]["metadata"][
            "easyworld_user_id"
        ],
        plan_code="PREMIUM",
        active=True,
    )

    provider = FakePaymentProvider(event)
    events = RecordingPaymentEventRepository()
    entitlements = FakeEntitlementService(entitlement_result)
    bridge = FakeWorldAccessBridge(
        RuntimeError("controlled world access failure"),
    )

    processor = ProcessStripeWebhook(
        provider,
        events,
        entitlements,
        bridge,
    )

    with pytest.raises(
        RuntimeError,
        match="controlled world access failure",
    ):
        await processor.execute_async(
            payload=b"payload",
            signature="signature",
        )

    assert entitlements.calls == [event]
    assert bridge.calls == [entitlement_result]
    assert events.mark_processed_calls == []
    assert events.mark_failed_calls == [
        (
            event.event_id,
            "controlled world access failure",
        ),
    ]
    assert events.has_processed(event.event_id) is False


@pytest.mark.asyncio
async def test_async_already_processed_skips_entitlement_and_world_access():
    event = _subscription_event()

    entitlement_result = SubscriptionEntitlementResult(
        beneficiary_user_id=event.payload["data"]["object"]["metadata"][
            "easyworld_user_id"
        ],
        plan_code="PREMIUM",
        active=True,
    )

    provider = FakePaymentProvider(event)
    events = RecordingPaymentEventRepository()
    entitlements = FakeEntitlementService(entitlement_result)
    bridge = FakeWorldAccessBridge()

    events.record_received(event)
    events.mark_processed(event.event_id)

    processor = ProcessStripeWebhook(
        provider,
        events,
        entitlements,
        bridge,
    )

    result = await processor.execute_async(
        payload=b"payload",
        signature="signature",
    )

    assert result == {
        "status": "already_processed",
        "event_id": event.event_id,
    }

    assert entitlements.calls == []
    assert bridge.calls == []
    assert events.mark_processed_calls == [event.event_id]
    assert events.mark_failed_calls == []
