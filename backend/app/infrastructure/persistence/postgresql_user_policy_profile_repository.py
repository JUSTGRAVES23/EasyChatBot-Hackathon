from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .user_policy_profile_models import UserPolicyProfileRecord


class PostgreSQLUserPolicyProfileRepository:
    """Durable PostgreSQL repository for user registration-policy state."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")

        self._session_factory = session_factory

    def get_by_user_id(
        self,
        *,
        user_id: UUID,
    ) -> UserPolicyProfileRecord | None:
        if user_id is None:
            raise ValueError("user_id cannot be None.")

        with self._session_factory() as session:
            return session.scalar(
                select(UserPolicyProfileRecord).where(
                    UserPolicyProfileRecord.user_id == user_id
                )
            )

    def upsert(
        self,
        *,
        user_id: UUID,
        policy_classification: str,
        guardian_required: bool,
        policy_version: str,
        policy_effective_at: datetime,
        jurisdiction: str | None = None,
    ) -> UserPolicyProfileRecord:
        if user_id is None:
            raise ValueError("user_id cannot be None.")

        if not policy_classification:
            raise ValueError("policy_classification cannot be empty.")

        if not policy_version:
            raise ValueError("policy_version cannot be empty.")

        if policy_effective_at is None:
            raise ValueError("policy_effective_at cannot be None.")

        with self._session_factory() as session:
            record = session.scalar(
                select(UserPolicyProfileRecord).where(
                    UserPolicyProfileRecord.user_id == user_id
                )
            )

            if record is None:
                record = UserPolicyProfileRecord(
                    user_id=user_id,
                    policy_classification=policy_classification,
                    guardian_required=guardian_required,
                    jurisdiction=jurisdiction,
                    policy_version=policy_version,
                    policy_effective_at=policy_effective_at,
                )
                session.add(record)
            else:
                record.policy_classification = policy_classification
                record.guardian_required = guardian_required
                record.jurisdiction = jurisdiction
                record.policy_version = policy_version
                record.policy_effective_at = policy_effective_at

            session.commit()
            session.refresh(record)

            return record


__all__ = ["PostgreSQLUserPolicyProfileRepository"]