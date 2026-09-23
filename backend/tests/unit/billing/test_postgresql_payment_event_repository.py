from datetime import datetime
from uuid import uuid4

from app.domain.payment.models import PaymentEvent
from app.infrastructure.payment.in_memory_repositories import (
    InMemoryPaymentEventRepository,
)


def test_payment_event_contract_accepts_verified_event() -> None:
    event = PaymentEvent(
        event_id=f"evt_{uuid4()}",
        event_type="checkout.session.completed",
        payload={"id": "example"},
    )

    repository = InMemoryPaymentEventRepository()

    assert repository.has_processed(event.event_id) is False

    repository.record_received(event)

    assert repository.has_processed(event.event_id) is False

    repository.mark_processed(event.event_id)

    assert repository.has_processed(event.event_id) is True


def test_payment_event_failed_processing_remains_retryable() -> None:
    event = PaymentEvent(
        event_id=f"evt_{uuid4()}",
        event_type="invoice.payment_failed",
        payload={"id": "example"},
    )

    repository = InMemoryPaymentEventRepository()

    repository.record_received(event)
    repository.mark_failed(
        event.event_id,
        "test failure",
    )

    assert repository.has_processed(event.event_id) is False
    assert repository.errors[event.event_id] == "test failure"
