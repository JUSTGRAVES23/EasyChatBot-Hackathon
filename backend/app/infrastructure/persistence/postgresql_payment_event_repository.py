from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.application.payment.ports import PaymentEventRepository
from app.domain.payment.models import PaymentEvent
from app.infrastructure.persistence.billing_models import StripeWebhookEventRecord


class PostgreSQLPaymentEventRepository(PaymentEventRepository):
    """Durable PostgreSQL implementation of Stripe webhook event storage.

    Responsibilities:
    - Persist verified Stripe webhook events.
    - Provide durable idempotency state.
    - Track processing failures.

    Does not:
    - Verify Stripe signatures.
    - Grant entitlements.
    - Apply payment business rules.
    """

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def has_processed(self, event_id: str) -> bool:
        if not event_id:
            raise ValueError("event_id cannot be empty.")

        with self._session_factory() as session:
            record = session.get(
                StripeWebhookEventRecord,
                event_id,
            )

            return record is not None and record.processed

    def record_received(self, event: PaymentEvent) -> None:
        if not isinstance(event, PaymentEvent):
            raise TypeError("event must be a PaymentEvent.")

        with self._session_factory() as session:
            existing = session.get(
                StripeWebhookEventRecord,
                event.event_id,
            )

            if existing is None:
                session.add(
                    StripeWebhookEventRecord(
                        stripe_event_id=event.event_id,
                        event_type=event.event_type,
                        processed=False,
                        processed_at=None,
                        payload=event.payload,
                        created_at=datetime.now(timezone.utc),
                    )
                )

            session.commit()

    def mark_processed(self, event_id: str) -> None:
        if not event_id:
            raise ValueError("event_id cannot be empty.")

        with self._session_factory() as session:
            record = session.get(
                StripeWebhookEventRecord,
                event_id,
            )

            if record is None:
                raise ValueError(
                    f"Stripe webhook event not found: {event_id!r}."
                )

            record.processed = True
            record.processed_at = datetime.now(timezone.utc)

            session.commit()

    def mark_failed(
        self,
        event_id: str,
        error: str,
    ) -> None:
        """Record that processing failed without deleting the event.

        The current persistence schema has no dedicated error column.
        Therefore the durable event remains recorded and unprocessed.
        The caller can retry the event safely.
        """

        if not event_id:
            raise ValueError("event_id cannot be empty.")

        if not error:
            raise ValueError("error cannot be empty.")

        with self._session_factory() as session:
            record = session.get(
                StripeWebhookEventRecord,
                event_id,
            )

            if record is None:
                raise ValueError(
                    f"Stripe webhook event not found: {event_id!r}."
                )

            record.processed = False
            record.processed_at = None

            session.commit()


__all__ = ["PostgreSQLPaymentEventRepository"]
