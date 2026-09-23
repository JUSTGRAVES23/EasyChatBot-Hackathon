"""Policy-evaluation adapter for Platform Intelligence escalation retries.

This adapter deliberately contains no retry-policy logic. It resolves the full
delivery record from the retry candidate and delegates eligibility to the
canonical PlatformIntelligenceEscalationRetryPolicyService.
"""

from __future__ import annotations

from datetime import datetime

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryRepository,
)
from app.application.operations_center.platform_intelligence_escalation_retry import (
    PlatformIntelligenceEscalationRetryPolicyService,
    PlatformIntelligenceEscalationRetryDecision,
)
from app.application.operations_center.platform_intelligence_escalation_retry_candidates import (
    PlatformIntelligenceEscalationRetryCandidate,
)


class PlatformIntelligenceRetryPolicyEvaluator:
    """Adapt retry candidates to the canonical retry policy service."""

    def __init__(
        self,
        *,
        delivery_repository: PlatformIntelligenceEscalationDeliveryRepository,
        retry_policy: PlatformIntelligenceEscalationRetryPolicyService,
    ) -> None:
        if delivery_repository is None:
            raise ValueError("delivery_repository cannot be None.")
        if retry_policy is None:
            raise ValueError("retry_policy cannot be None.")

        self._delivery_repository = delivery_repository
        self._retry_policy = retry_policy

    async def evaluate(
        self,
        *,
        candidate: PlatformIntelligenceEscalationRetryCandidate,
        reference_at: datetime,
    ) -> bool:
        """Return whether the candidate is currently eligible for retry.

        Missing delivery state fails closed. All retry eligibility decisions
        remain owned by PlatformIntelligenceEscalationRetryPolicyService.
        """
        if candidate is None:
            raise ValueError("candidate cannot be None.")

        record = await self._delivery_repository.get_by_notification_key(
            candidate.notification_key
        )
        if record is None:
            return False

        result = self._retry_policy.evaluate(
            record=record,
            reference_at=reference_at,
        )

        return (
            result.decision
            is PlatformIntelligenceEscalationRetryDecision.ELIGIBLE
        )
