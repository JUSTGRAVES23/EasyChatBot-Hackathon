from app.domain.payment.models import PaymentEvent
from app.infrastructure.payment.in_memory_repositories import InMemoryPaymentEventRepository


def test_event_is_processed_once():
    repo = InMemoryPaymentEventRepository()
    event = PaymentEvent(event_id="evt_123", event_type="invoice.paid", payload={})

    assert not repo.has_processed(event.event_id)
    repo.record_received(event)
    repo.mark_processed(event.event_id)

    assert repo.has_processed(event.event_id)

    # A retry remains recognized as already processed.
    assert repo.has_processed(event.event_id)
