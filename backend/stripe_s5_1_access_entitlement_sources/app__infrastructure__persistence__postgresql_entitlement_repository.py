from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.persistence.billing_models import EntitlementRecord


class PostgreSQLEntitlementRepository:
    """Durable PostgreSQL repository for EASYWORLD entitlements."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
    ) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def get(
        self,
        *,
        user_id: str,
        plan_code: str,
    ) -> EntitlementRecord | None:
        if not user_id:
            raise ValueError("user_id cannot be empty.")

        if not plan_code:
            raise ValueError("plan_code cannot be empty.")

        with self._session_factory() as session:
            return session.scalar(
                select(EntitlementRecord).where(
                    EntitlementRecord.user_id == user_id,
                    EntitlementRecord.plan_code == plan_code,
                )
            )

    def get_for_user(
        self,
        user_id: str,
    ) -> list[EntitlementRecord]:
        if not user_id:
            raise ValueError("user_id cannot be empty.")

        with self._session_factory() as session:
            return list(
                session.scalars(
                    select(EntitlementRecord)
                    .where(EntitlementRecord.user_id == user_id)
                    .order_by(EntitlementRecord.created_at.desc())
                ).all()
            )

    def upsert(
        self,
        *,
        user_id: str,
        plan_code: str,
        ai_credits: int = 0,
        agent_access: bool = False,
        premium_models: bool = False,
        priority_processing: bool = False,
        active: bool = True,
    ) -> EntitlementRecord:
        if not user_id:
            raise ValueError("user_id cannot be empty.")

        if not plan_code:
            raise ValueError("plan_code cannot be empty.")

        if ai_credits < 0:
            raise ValueError("ai_credits cannot be negative.")

        with self._session_factory() as session:
            record = session.scalar(
                select(EntitlementRecord).where(
                    EntitlementRecord.user_id == user_id,
                    EntitlementRecord.plan_code == plan_code,
                )
            )

            if record is None:
                record = EntitlementRecord(
                    user_id=user_id,
                    plan_code=plan_code,
                    ai_credits=ai_credits,
                    agent_access=agent_access,
                    premium_models=premium_models,
                    priority_processing=priority_processing,
                    active=active,
                )
                session.add(record)
            else:
                record.ai_credits = ai_credits
                record.agent_access = agent_access
                record.premium_models = premium_models
                record.priority_processing = priority_processing
                record.active = active

            session.commit()
            session.refresh(record)

            return record


__all__ = ["PostgreSQLEntitlementRepository"]
