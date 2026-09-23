"""Contracts for durable PI escalation delivery audit history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class PlatformIntelligenceEscalationDeliveryAuditStatus(StrEnum):
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationDeliveryAuditRecord:
    """Immutable append-only audit event for one PI delivery attempt."""

    audit_id: UUID
    notification_key: str
    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    correlation_id: str
    attempt: int
    status: PlatformIntelligenceEscalationDeliveryAuditStatus
    provider_message_id: str | None = None
    error_code: str | None = None
    occurred_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in (
            "notification_key", "recommendation_id", "risk_decision_id",
            "review_item_id", "correlation_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be nonblank.")
        if self.attempt < 1:
            raise ValueError("attempt must be at least 1.")
        if self.occurred_at is not None and (
            self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None
        ):
            raise ValueError("occurred_at must be timezone-aware.")
        if (
            self.status is PlatformIntelligenceEscalationDeliveryAuditStatus.SUCCEEDED
            and not self.provider_message_id
        ):
            raise ValueError("SUCCEEDED audit events require provider_message_id.")
        if (
            self.status is PlatformIntelligenceEscalationDeliveryAuditStatus.FAILED
            and not self.error_code
        ):
            raise ValueError("FAILED audit events require error_code.")
        if (
            self.status is PlatformIntelligenceEscalationDeliveryAuditStatus.SUCCEEDED
            and self.error_code is not None
        ):
            raise ValueError("SUCCEEDED audit events cannot contain error_code.")


class PlatformIntelligenceEscalationDeliveryAuditRepository:
    """Read/append port for PI delivery audit history."""

    async def append(self, record: PlatformIntelligenceEscalationDeliveryAuditRecord) -> None:
        raise NotImplementedError

    async def list_by_notification_key(
        self, notification_key: str
    ) -> tuple[PlatformIntelligenceEscalationDeliveryAuditRecord, ...]:
        raise NotImplementedError
