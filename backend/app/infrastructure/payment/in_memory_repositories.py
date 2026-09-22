from __future__ import annotations

from app.domain.payment.models import PaymentEvent


class InMemoryPaymentEventRepository:
    """Development/test implementation. Replace with the canonical EASYWORLD DB repository."""

    def __init__(self):
        self.events: dict[str, PaymentEvent] = {}
        self.status: dict[str, str] = {}
        self.errors: dict[str, str] = {}

    def has_processed(self, event_id: str) -> bool:
        return self.status.get(event_id) == "processed"

    def record_received(self, event: PaymentEvent) -> None:
        self.events.setdefault(event.event_id, event)
        self.status.setdefault(event.event_id, "received")

    def mark_processed(self, event_id: str) -> None:
        self.status[event_id] = "processed"

    def mark_failed(self, event_id: str, error: str) -> None:
        self.status[event_id] = "failed"
        self.errors[event_id] = error
