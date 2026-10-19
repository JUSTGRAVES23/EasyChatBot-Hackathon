"""PostgreSQL persistence adapter for PI escalation delivery."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryRecord,
    PlatformIntelligenceEscalationDeliveryRepository,
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_delivery_audit import (
    PlatformIntelligenceEscalationDeliveryAuditRecord,
    PlatformIntelligenceEscalationDeliveryAuditStatus,
)
from app.infrastructure.operations_center.sqlalchemy_platform_intelligence_escalation_delivery_audit_repository import (
    SqlAlchemyPlatformIntelligenceEscalationDeliveryAuditRepository,
)


class SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
    PlatformIntelligenceEscalationDeliveryRepository
):
    _TABLE = "platform_intelligence_escalation_deliveries"

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        if session_factory is None:
            raise ValueError("session_factory cannot be None.")
        self._session_factory = session_factory

    async def get_by_notification_key(self, notification_key: str):
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT notification_key, recommendation_id,
                           risk_decision_id, review_item_id, correlation_id,
                           attempt, status, provider_message_id, error_code,
                           created_at, updated_at
                    FROM {self._TABLE}
                    WHERE notification_key = :notification_key
                    """
                ),
                {"notification_key": notification_key},
            )
            row = result.mappings().first()
            return None if row is None else self._to_record(row)

    async def list_retry_candidates(self, *, limit: int):
        if limit < 1:
            raise ValueError("limit must be at least 1.")
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    SELECT notification_key, recommendation_id,
                           risk_decision_id, review_item_id, correlation_id,
                           attempt, status, provider_message_id, error_code,
                           created_at, updated_at
                    FROM {self._TABLE}
                    WHERE status IN (:failed, :started)
                    ORDER BY updated_at ASC NULLS FIRST, notification_key ASC
                    LIMIT :limit
                    """
                ),
                {
                    "failed": PlatformIntelligenceEscalationDeliveryStatus.FAILED.value,
                    "started": PlatformIntelligenceEscalationDeliveryStatus.STARTED.value,
                    "limit": limit,
                },
            )
            return tuple(self._to_record(row) for row in result.mappings().all())

    async def claim_retry_candidate(
        self, *, notification_key: str, claim_token: str,
        claimed_at: datetime, lease_expires_at: datetime,
    ) -> bool:
        if not notification_key.strip():
            raise ValueError("notification_key must be nonblank.")
        if not claim_token.strip():
            raise ValueError("claim_token must be nonblank.")
        if claimed_at.tzinfo is None or claimed_at.utcoffset() is None:
            raise ValueError("claimed_at must be timezone-aware.")
        if lease_expires_at.tzinfo is None or lease_expires_at.utcoffset() is None:
            raise ValueError("lease_expires_at must be timezone-aware.")
        if lease_expires_at <= claimed_at:
            raise ValueError("lease_expires_at must be after claimed_at.")

        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    UPDATE {self._TABLE}
                    SET claim_token = :claim_token,
                        claimed_at = :claimed_at,
                        lease_expires_at = :lease_expires_at
                    WHERE notification_key = :notification_key
                      AND status IN (:failed, :started)
                      AND (
                          lease_expires_at IS NULL
                          OR lease_expires_at <= :claimed_at
                      )
                    """
                ),
                {
                    "notification_key": notification_key,
                    "claim_token": claim_token,
                    "claimed_at": claimed_at,
                    "lease_expires_at": lease_expires_at,
                    "failed": PlatformIntelligenceEscalationDeliveryStatus.FAILED.value,
                    "started": PlatformIntelligenceEscalationDeliveryStatus.STARTED.value,
                },
            )
            await session.commit()
            return result.rowcount == 1

    async def create_started(
        self, *, notification_key: str, recommendation_id: str,
        risk_decision_id: str, review_item_id: str, correlation_id: str,
    ):
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            await session.execute(
                text(
                    f"""
                    INSERT INTO {self._TABLE} (
                        notification_key, recommendation_id, risk_decision_id,
                        review_item_id, correlation_id, attempt, status,
                        provider_message_id, error_code, created_at, updated_at,
                        claim_token, claimed_at, lease_expires_at
                    )
                    VALUES (
                        :notification_key, :recommendation_id, :risk_decision_id,
                        :review_item_id, :correlation_id, 1, :status,
                        NULL, NULL, :created_at, :updated_at,
                        NULL, NULL, NULL
                    )
                    """
                ),
                {
                    "notification_key": notification_key,
                    "recommendation_id": recommendation_id,
                    "risk_decision_id": risk_decision_id,
                    "review_item_id": review_item_id,
                    "correlation_id": correlation_id,
                    "status": PlatformIntelligenceEscalationDeliveryStatus.STARTED.value,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            await self._insert_audit(
                session,
                notification_key=notification_key,
                recommendation_id=recommendation_id,
                risk_decision_id=risk_decision_id,
                review_item_id=review_item_id,
                correlation_id=correlation_id,
                attempt=1,
                status=PlatformIntelligenceEscalationDeliveryAuditStatus.STARTED,
                occurred_at=now,
            )
            await session.commit()

        record = await self.get_by_notification_key(notification_key)
        if record is None:
            raise RuntimeError("Created PI escalation delivery could not be reloaded.")
        return record

    async def mark_succeeded(
        self, *, notification_key: str, provider_message_id: str | None,
        claim_token: str | None = None,
    ):
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    UPDATE {self._TABLE}
                    SET status = :status,
                        provider_message_id = :provider_message_id,
                        error_code = NULL,
                        updated_at = :updated_at,
                        claim_token = NULL,
                        claimed_at = NULL,
                        lease_expires_at = NULL
                    WHERE notification_key = :notification_key
                      AND status = :started
                      AND (
                          (CAST(:claim_token AS TEXT) IS NULL AND claim_token IS NULL)
                          OR (
                              CAST(:claim_token AS TEXT) IS NOT NULL
                              AND claim_token = :claim_token
                              AND lease_expires_at > :updated_at
                          )
                      )
                    RETURNING notification_key, recommendation_id,
                              risk_decision_id, review_item_id, correlation_id,
                              attempt, status, provider_message_id,
                              error_code, created_at, updated_at
                    """
                ),
                {
                    "notification_key": notification_key,
                    "claim_token": claim_token,
                    "started": PlatformIntelligenceEscalationDeliveryStatus.STARTED.value,
                    "status": PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED.value,
                    "provider_message_id": provider_message_id,
                    "updated_at": now,
                },
            )
            row = result.mappings().first()
            if row is None:
                await session.rollback()
                raise KeyError(f"Unknown PI escalation notification key: {notification_key}")

            record = self._to_record(row)
            if not provider_message_id:
                await session.rollback()
                raise ValueError("Successful PI delivery requires provider_message_id.")

            await self._insert_audit(
                session,
                notification_key=record.notification_key,
                recommendation_id=record.recommendation_id,
                risk_decision_id=record.risk_decision_id,
                review_item_id=record.review_item_id,
                correlation_id=record.correlation_id,
                attempt=record.attempt,
                status=PlatformIntelligenceEscalationDeliveryAuditStatus.SUCCEEDED,
                provider_message_id=provider_message_id,
                occurred_at=now,
            )
            await session.commit()
            return record

    async def mark_failed(
        self, *, notification_key: str, error_code: str,
        claim_token: str | None = None,
    ):
        if not error_code.strip():
            raise ValueError("error_code must be nonblank.")
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    UPDATE {self._TABLE}
                    SET status = :status,
                        provider_message_id = NULL,
                        error_code = :error_code,
                        updated_at = :updated_at,
                        claim_token = NULL,
                        claimed_at = NULL,
                        lease_expires_at = NULL
                    WHERE notification_key = :notification_key
                      AND status = :started
                      AND (
                          (CAST(:claim_token AS TEXT) IS NULL AND claim_token IS NULL)
                          OR (
                              CAST(:claim_token AS TEXT) IS NOT NULL
                              AND claim_token = :claim_token
                              AND lease_expires_at > :updated_at
                          )
                      )
                    RETURNING notification_key, recommendation_id,
                              risk_decision_id, review_item_id, correlation_id,
                              attempt, status, provider_message_id,
                              error_code, created_at, updated_at
                    """
                ),
                {
                    "notification_key": notification_key,
                    "claim_token": claim_token,
                    "started": PlatformIntelligenceEscalationDeliveryStatus.STARTED.value,
                    "status": PlatformIntelligenceEscalationDeliveryStatus.FAILED.value,
                    "error_code": error_code,
                    "updated_at": now,
                },
            )
            row = result.mappings().first()
            if row is None:
                await session.rollback()
                raise KeyError(f"Unknown PI escalation notification key: {notification_key}")

            record = self._to_record(row)
            await self._insert_audit(
                session,
                notification_key=record.notification_key,
                recommendation_id=record.recommendation_id,
                risk_decision_id=record.risk_decision_id,
                review_item_id=record.review_item_id,
                correlation_id=record.correlation_id,
                attempt=record.attempt,
                status=PlatformIntelligenceEscalationDeliveryAuditStatus.FAILED,
                error_code=error_code,
                occurred_at=now,
            )
            await session.commit()
            return record

    async def start_retry(self, *, notification_key: str, claim_token: str):
        now = datetime.now(timezone.utc)
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    f"""
                    UPDATE {self._TABLE}
                    SET attempt = attempt + 1,
                        status = :started,
                        provider_message_id = NULL,
                        error_code = NULL,
                        updated_at = :updated_at
                    WHERE notification_key = :notification_key
                      AND status = :failed
                      AND claim_token = :claim_token
                      AND lease_expires_at > :updated_at
                    RETURNING notification_key, recommendation_id,
                              risk_decision_id, review_item_id, correlation_id,
                              attempt, status, provider_message_id,
                              error_code, created_at, updated_at
                    """
                ),
                {
                    "notification_key": notification_key,
                    "claim_token": claim_token,
                    "started": PlatformIntelligenceEscalationDeliveryStatus.STARTED.value,
                    "failed": PlatformIntelligenceEscalationDeliveryStatus.FAILED.value,
                    "updated_at": now,
                },
            )
            row = result.mappings().first()
            if row is None:
                await session.rollback()
                raise RuntimeError(
                    "PI escalation retry claim is stale, expired, or no longer "
                    "eligible; delivery state was not changed."
                )

            record = self._to_record(row)
            await self._insert_audit(
                session,
                notification_key=record.notification_key,
                recommendation_id=record.recommendation_id,
                risk_decision_id=record.risk_decision_id,
                review_item_id=record.review_item_id,
                correlation_id=record.correlation_id,
                attempt=record.attempt,
                status=PlatformIntelligenceEscalationDeliveryAuditStatus.STARTED,
                occurred_at=now,
            )
            await session.commit()
            return record

    @staticmethod
    async def _insert_audit(
        session: AsyncSession,
        *,
        notification_key: str,
        recommendation_id: str,
        risk_decision_id: str,
        review_item_id: str,
        correlation_id: str,
        attempt: int,
        status: PlatformIntelligenceEscalationDeliveryAuditStatus,
        occurred_at: datetime,
        provider_message_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        record = PlatformIntelligenceEscalationDeliveryAuditRecord(
            audit_id=uuid4(),
            notification_key=notification_key,
            recommendation_id=recommendation_id,
            risk_decision_id=risk_decision_id,
            review_item_id=review_item_id,
            correlation_id=correlation_id,
            attempt=attempt,
            status=status,
            provider_message_id=provider_message_id,
            error_code=error_code,
            occurred_at=occurred_at,
        )
        await SqlAlchemyPlatformIntelligenceEscalationDeliveryAuditRepository.insert_with_session(
            session, record
        )

    @staticmethod
    def _to_record(row: Mapping[str, Any]):
        return PlatformIntelligenceEscalationDeliveryRecord(
            notification_key=str(row["notification_key"]),
            recommendation_id=str(row["recommendation_id"]),
            risk_decision_id=str(row["risk_decision_id"]),
            review_item_id=str(row["review_item_id"]),
            correlation_id=str(row["correlation_id"]),
            attempt=int(row["attempt"]),
            status=PlatformIntelligenceEscalationDeliveryStatus(str(row["status"])),
            provider_message_id=row["provider_message_id"],
            error_code=row["error_code"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
