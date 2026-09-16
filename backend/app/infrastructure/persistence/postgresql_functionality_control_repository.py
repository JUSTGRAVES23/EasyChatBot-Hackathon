from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.application.provider_management.functionality_operational_control_service import (
    OperationalControlResult,
)
from app.infrastructure.persistence.functionality_control_records import (
    FunctionalityControlAuditRecord,
    FunctionalityControlStateRecord,
)


class PostgreSQLFunctionalityControlRepository:
    """Durable functionality control state and audit repository."""

    def __init__(self, session_factory) -> None:
        if session_factory is None:
            raise ValueError("session_factory is required.")

        self._session_factory = session_factory

    def get_availability(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> str:
        with self._session_factory() as session:
            record = session.scalar(
                select(FunctionalityControlStateRecord).where(
                    FunctionalityControlStateRecord.environment
                    == environment,
                    FunctionalityControlStateRecord.functionality_id
                    == functionality_id,
                )
            )

        if record is None:
            return "enabled"

        return record.availability

    def get_last_action(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> OperationalControlResult | None:
        with self._session_factory() as session:
            record = session.scalar(
                select(FunctionalityControlStateRecord).where(
                    FunctionalityControlStateRecord.environment
                    == environment,
                    FunctionalityControlStateRecord.functionality_id
                    == functionality_id,
                )
            )

        if record is None or record.changed_at is None:
            return None

        return OperationalControlResult(
            functionality_id=record.functionality_id,
            environment=record.environment,
            availability=record.availability,
            action=record.action or "unknown",
            reason=record.reason,
            changed_at=record.changed_at,
            changed_by=record.changed_by or "unknown",
        )

    def record_transition(
        self,
        *,
        functionality_id: str,
        environment: str,
        availability: str,
        action: str,
        reason: str | None,
        changed_at: datetime,
        changed_by: str,
    ) -> OperationalControlResult:
        with self._session_factory() as session:
            state = session.scalar(
                select(FunctionalityControlStateRecord).where(
                    FunctionalityControlStateRecord.environment
                    == environment,
                    FunctionalityControlStateRecord.functionality_id
                    == functionality_id,
                )
            )

            if state is None:
                state = FunctionalityControlStateRecord(
                    functionality_id=functionality_id,
                    environment=environment,
                )
                session.add(state)

            state.availability = availability
            state.action = action
            state.reason = reason
            state.changed_at = changed_at
            state.changed_by = changed_by

            session.add(
                FunctionalityControlAuditRecord(
                    functionality_id=functionality_id,
                    environment=environment,
                    action=action,
                    availability=availability,
                    changed_by=changed_by,
                    reason=reason,
                    changed_at=changed_at,
                )
            )

            session.commit()

        return OperationalControlResult(
            functionality_id=functionality_id,
            environment=environment,
            availability=availability,
            action=action,
            reason=reason,
            changed_at=changed_at,
            changed_by=changed_by,
        )