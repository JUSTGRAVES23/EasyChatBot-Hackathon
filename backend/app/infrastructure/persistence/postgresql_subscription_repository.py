from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.persistence.billing_models import SubscriptionRecord


class PostgreSQLSubscriptionRepository:
    """Durable PostgreSQL repository for EASYWORLD subscriptions."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def get_by_stripe_subscription_id(
        self,
        stripe_subscription_id: str,
    ) -> SubscriptionRecord | None:
        if not stripe_subscription_id:
            raise ValueError("stripe_subscription_id cannot be empty.")

        with self._session_factory() as session:
            return session.scalar(
                select(SubscriptionRecord).where(
                    SubscriptionRecord.stripe_subscription_id
                    == stripe_subscription_id
                )
            )

    def get_by_beneficiary_user_id(
        self,
        beneficiary_user_id: str,
    ) -> list[SubscriptionRecord]:
        if not beneficiary_user_id:
            raise ValueError("beneficiary_user_id cannot be empty.")

        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(SubscriptionRecord)
                    .where(
                        SubscriptionRecord.beneficiary_user_id
                        == beneficiary_user_id
                    )
                    .order_by(SubscriptionRecord.created_at.desc())
                ).all()
            )

    def upsert(
        self,
        *,
        beneficiary_user_id: str,
        payer_user_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        stripe_price_id: str,
        plan_code: str,
        status: str,
        current_period_start: datetime | None = None,
        current_period_end: datetime | None = None,
        cancel_at_period_end: bool = False,
    ) -> SubscriptionRecord:
        required_values = {
            "beneficiary_user_id": beneficiary_user_id,
            "payer_user_id": payer_user_id,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_price_id": stripe_price_id,
            "plan_code": plan_code,
            "status": status,
        }

        for field, value in required_values.items():
            if not value:
                raise ValueError(f"{field} cannot be empty.")

        with self._session_factory() as session:
            record = session.scalar(
                select(SubscriptionRecord).where(
                    SubscriptionRecord.stripe_subscription_id
                    == stripe_subscription_id
                )
            )

            if record is None:
                record = SubscriptionRecord(
                    beneficiary_user_id=beneficiary_user_id,
                    payer_user_id=payer_user_id,
                    stripe_customer_id=stripe_customer_id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_price_id=stripe_price_id,
                    plan_code=plan_code,
                    status=status,
                    current_period_start=current_period_start,
                    current_period_end=current_period_end,
                    cancel_at_period_end=cancel_at_period_end,
                )
                session.add(record)
            else:
                record.beneficiary_user_id = beneficiary_user_id
                record.payer_user_id = payer_user_id
                record.stripe_customer_id = stripe_customer_id
                record.stripe_price_id = stripe_price_id
                record.plan_code = plan_code
                record.status = status
                record.current_period_start = current_period_start
                record.current_period_end = current_period_end
                record.cancel_at_period_end = cancel_at_period_end

            session.commit()
            session.refresh(record)

            return record

    def delete_by_stripe_subscription_id(
        self,
        stripe_subscription_id: str,
    ) -> None:
        if not stripe_subscription_id:
            raise ValueError("stripe_subscription_id cannot be empty.")

        with self._session_factory() as session:
            record = session.scalar(
                select(SubscriptionRecord).where(
                    SubscriptionRecord.stripe_subscription_id
                    == stripe_subscription_id
                )
            )

            if record is not None:
                session.delete(record)
                session.commit()


__all__ = ["PostgreSQLSubscriptionRepository"]
