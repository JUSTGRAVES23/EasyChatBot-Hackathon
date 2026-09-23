from __future__ import annotations

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_candidates import (
    PlatformIntelligenceEscalationRetryCandidate,
    PlatformIntelligenceEscalationRetryCandidateBatch,
    PlatformIntelligenceEscalationRetryCandidateRepository,
)


class PlatformIntelligenceEscalationRetryCandidateDiscoveryService:
    """Discover durable retry work without executing it.

    This boundary deliberately does not:
    - call the retry policy;
    - mutate delivery state;
    - send email;
    - schedule work;
    - claim/lock candidates.

    Policy eligibility and execution remain separate steps.
    """

    def __init__(
        self,
        *,
        repository: PlatformIntelligenceEscalationRetryCandidateRepository,
    ) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")

        self._repository = repository

    async def discover(
        self,
        *,
        limit: int = 100,
    ) -> PlatformIntelligenceEscalationRetryCandidateBatch:
        if limit < 1:
            raise ValueError("limit must be at least 1.")

        records = await self._repository.list_retry_candidates(
            limit=limit,
        )

        candidates: list[PlatformIntelligenceEscalationRetryCandidate] = []

        for record in records:
            if record.status not in (
                PlatformIntelligenceEscalationDeliveryStatus.FAILED,
                PlatformIntelligenceEscalationDeliveryStatus.STARTED,
            ):
                continue

            candidates.append(
                PlatformIntelligenceEscalationRetryCandidate(
                    notification_key=record.notification_key,
                    recommendation_id=record.recommendation_id,
                    risk_decision_id=record.risk_decision_id,
                    review_item_id=record.review_item_id,
                    correlation_id=record.correlation_id,
                    attempt=record.attempt,
                    status=record.status.value,
                    error_code=record.error_code,
                    updated_at=record.updated_at,
                )
            )

        candidates.sort(
            key=lambda candidate: (
                candidate.updated_at is None,
                candidate.updated_at,
                candidate.notification_key,
            )
        )

        return PlatformIntelligenceEscalationRetryCandidateBatch(
            candidates=tuple(candidates),
            limit=limit,
        )
