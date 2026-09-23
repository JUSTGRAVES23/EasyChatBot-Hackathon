from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.persistence.billing_models import (
    ParentalConsentRecord,
)


class PostgreSQLParentalConsentRepository:
    """Durable PostgreSQL repository for purpose-specific parental consent."""

    PAYMENT_CONSENT_TYPE = "PAID_SUBSCRIPTION"

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def has_active_payment_consent(
        self,
        *,
        parent_user_id: str,
        child_user_id: str,
    ) -> bool:
        if not parent_user_id:
            raise ValueError("parent_user_id cannot be empty.")

        if not child_user_id:
            raise ValueError("child_user_id cannot be empty.")

        now = datetime.now(timezone.utc)

        with self._session_factory() as session:
            record = session.scalar(
                select(ParentalConsentRecord).where(
                    ParentalConsentRecord.parent_user_id
                    == parent_user_id,
                    ParentalConsentRecord.child_user_id
                    == child_user_id,
                    ParentalConsentRecord.consent_type
                    == self.PAYMENT_CONSENT_TYPE,
                    ParentalConsentRecord.status == "active",
                )
            )

            if record is None:
                return False

            if record.expires_at is not None and record.expires_at <= now:
                return False

            if record.revoked_at is not None:
                return False

            return True

    def grant_payment_consent(
        self,
        *,
        parent_user_id: str,
        child_user_id: str,
        expires_at: datetime | None = None,
    ) -> ParentalConsentRecord:
        if not parent_user_id:
            raise ValueError("parent_user_id cannot be empty.")

        if not child_user_id:
            raise ValueError("child_user_id cannot be empty.")

        if parent_user_id == child_user_id:
            raise ValueError(
                "parent_user_id and child_user_id must be different."
            )

        now = datetime.now(timezone.utc)

        with self._session_factory() as session:
            record = session.scalar(
                select(ParentalConsentRecord).where(
                    ParentalConsentRecord.parent_user_id
                    == parent_user_id,
                    ParentalConsentRecord.child_user_id
                    == child_user_id,
                    ParentalConsentRecord.consent_type
                    == self.PAYMENT_CONSENT_TYPE,
                )
            )

            if record is None:
                record = ParentalConsentRecord(
                    parent_user_id=parent_user_id,
                    child_user_id=child_user_id,
                    consent_type=self.PAYMENT_CONSENT_TYPE,
                    status="active",
                    granted_at=now,
                    revoked_at=None,
                    expires_at=expires_at,
                    created_at=now,
                    updated_at=now,
                )
                session.add(record)
            else:
                record.status = "active"
                record.granted_at = now
                record.revoked_at = None
                record.expires_at = expires_at
                record.updated_at = now

            session.commit()
            session.refresh(record)

            return record

    def revoke_payment_consent(
        self,
        *,
        parent_user_id: str,
        child_user_id: str,
    ) -> None:
        if not parent_user_id:
            raise ValueError("parent_user_id cannot be empty.")

        if not child_user_id:
            raise ValueError("child_user_id cannot be empty.")

        with self._session_factory() as session:
            record = session.scalar(
                select(ParentalConsentRecord).where(
                    ParentalConsentRecord.parent_user_id
                    == parent_user_id,
                    ParentalConsentRecord.child_user_id
                    == child_user_id,
                    ParentalConsentRecord.consent_type
                    == self.PAYMENT_CONSENT_TYPE,
                )
            )

            if record is None:
                return

            record.status = "revoked"
            record.revoked_at = datetime.now(timezone.utc)
            record.updated_at = datetime.now(timezone.utc)

            session.commit()


__all__ = [
    "PostgreSQLParentalConsentRepository",
]
