from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryRecord,
)


class PlatformIntelligenceEscalationRetryCandidateRepository(Protocol):
    """Read-only application boundary for retry candidate discovery."""

    async def list_retry_candidates(
        self,
        *,
        limit: int,
    ) -> Sequence[PlatformIntelligenceEscalationDeliveryRecord]:
        """Return durable FAILED/STARTED delivery records for policy evaluation."""
        ...


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationRetryCandidate:
    """Durable delivery state selected for policy evaluation."""

    notification_key: str
    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    correlation_id: str
    attempt: int
    status: str
    error_code: str | None
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationRetryCandidateBatch:
    """Deterministic discovery result; no retry is executed here."""

    candidates: tuple[PlatformIntelligenceEscalationRetryCandidate, ...]
    limit: int
