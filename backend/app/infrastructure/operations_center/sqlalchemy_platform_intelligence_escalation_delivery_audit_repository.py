"""PostgreSQL read/append adapter for PI delivery audit history."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.operations_center.platform_intelligence_escalation_delivery_audit import (
    PlatformIntelligenceEscalationDeliveryAuditRecord,
    PlatformIntelligenceEscalationDeliveryAuditRepository,
    PlatformIntelligenceEscalationDeliveryAuditStatus,
)


class SqlAlchemyPlatformIntelligenceEscalationDeliveryAuditRepository(
    PlatformIntelligenceEscalationDeliveryAuditRepository
):
    _TABLE = "platform_intelligence_escalation_delivery_audit"

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def append(self, record: PlatformIntelligenceEscalationDeliveryAuditRecord) -> None:
        if record.occurred_at is None:
            raise ValueError("occurred_at is required for durable audit persistence.")
        async with self._session_factory() as session:
            await self._insert(session, record)
            await session.commit()

    async def list_by_notification_key(self, notification_key: str):
        if not notification_key.strip():
            raise ValueError("notification_key must be nonblank.")
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT audit_id, notification_key, recommendation_id,
                           risk_decision_id, review_item_id, correlation_id,
                           attempt, status, provider_message_id, error_code,
                           occurred_at
                    FROM {self._TABLE}
                    WHERE notification_key = :notification_key
                    ORDER BY occurred_at ASC, audit_id ASC
                    """
                ),
                {"notification_key": notification_key},
            )
            return tuple(self._to_record(row) for row in result.mappings().all())

    @classmethod
    async def insert_with_session(
        cls,
        session: AsyncSession,
        record: PlatformIntelligenceEscalationDeliveryAuditRecord,
    ) -> None:
        if record.occurred_at is None:
            raise ValueError("occurred_at is required for durable audit persistence.")
        await cls._insert(session, record)

    @classmethod
    async def _insert(
        cls,
        session: AsyncSession,
        record: PlatformIntelligenceEscalationDeliveryAuditRecord,
    ) -> None:
        await session.execute(
            text(
                f"""
                INSERT INTO {cls._TABLE} (
                    audit_id, notification_key, recommendation_id,
                    risk_decision_id, review_item_id, correlation_id,
                    attempt, status, provider_message_id, error_code,
                    occurred_at
                )
                VALUES (
                    :audit_id, :notification_key, :recommendation_id,
                    :risk_decision_id, :review_item_id, :correlation_id,
                    :attempt, :status, :provider_message_id, :error_code,
                    :occurred_at
                )
                """
            ),
            {
                "audit_id": record.audit_id,
                "notification_key": record.notification_key,
                "recommendation_id": record.recommendation_id,
                "risk_decision_id": record.risk_decision_id,
                "review_item_id": record.review_item_id,
                "correlation_id": record.correlation_id,
                "attempt": record.attempt,
                "status": record.status.value,
                "provider_message_id": record.provider_message_id,
                "error_code": record.error_code,
                "occurred_at": record.occurred_at,
            },
        )

    @staticmethod
    def _to_record(row: Mapping[str, Any]) -> PlatformIntelligenceEscalationDeliveryAuditRecord:
        return PlatformIntelligenceEscalationDeliveryAuditRecord(
            audit_id=UUID(str(row["audit_id"])),
            notification_key=str(row["notification_key"]),
            recommendation_id=str(row["recommendation_id"]),
            risk_decision_id=str(row["risk_decision_id"]),
            review_item_id=str(row["review_item_id"]),
            correlation_id=str(row["correlation_id"]),
            attempt=int(row["attempt"]),
            status=PlatformIntelligenceEscalationDeliveryAuditStatus(str(row["status"])),
            provider_message_id=row["provider_message_id"],
            error_code=row["error_code"],
            occurred_at=row["occurred_at"],
        )
