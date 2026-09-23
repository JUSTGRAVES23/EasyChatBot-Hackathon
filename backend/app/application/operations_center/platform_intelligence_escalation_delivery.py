"""Contracts for governed Platform Intelligence escalation delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PlatformIntelligenceEscalationDeliveryStatus(StrEnum):
    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationDeliveryRecord:
    """Durable state for one PI escalation notification key."""

    notification_key: str
    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    correlation_id: str
    attempt: int
    status: PlatformIntelligenceEscalationDeliveryStatus
    provider_message_id: str | None = None
    error_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlatformIntelligenceEscalationDeliveryRepository:
    """Application port for durable PI escalation delivery state."""

    async def get_by_notification_key(
        self,
        notification_key: str,
    ) -> PlatformIntelligenceEscalationDeliveryRecord | None:
        raise NotImplementedError

    async def create_started(
        self,
        *,
        notification_key: str,
        recommendation_id: str,
        risk_decision_id: str,
        review_item_id: str,
        correlation_id: str,
    ) -> PlatformIntelligenceEscalationDeliveryRecord:
        raise NotImplementedError

    async def mark_succeeded(
        self,
        *,
        notification_key: str,
        provider_message_id: str | None,
    ) -> PlatformIntelligenceEscalationDeliveryRecord:
        raise NotImplementedError

    async def mark_failed(
        self,
        *,
        notification_key: str,
        error_code: str,
    ) -> PlatformIntelligenceEscalationDeliveryRecord:
        raise NotImplementedError

    async def start_retry(
        self,
        *,
        notification_key: str,
    ) -> PlatformIntelligenceEscalationDeliveryRecord:
        raise NotImplementedError
