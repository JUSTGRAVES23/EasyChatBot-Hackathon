"""Application service for controlled retry candidate claiming."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import uuid4

from app.application.operations_center.platform_intelligence_escalation_retry_claims import (
    PlatformIntelligenceEscalationRetryClaim,
    RetryCandidateClaimStatus,
)


class PlatformIntelligenceEscalationRetryClaimRepository(Protocol):
    async def claim_retry_candidate(
        self,
        *,
        notification_key: str,
        claim_token: str,
        claimed_at: datetime,
        lease_expires_at: datetime,
    ) -> bool: ...


class PlatformIntelligenceEscalationRetryClaimService:
    """Claims a candidate for one bounded execution attempt.

    Claiming is coordination only. It does not evaluate retry policy, send
    email, mutate the delivery lifecycle beyond the lease, or authorize the
    escalation itself.
    """

    def __init__(
        self,
        repository: PlatformIntelligenceEscalationRetryClaimRepository,
        *,
        lease_seconds: int = 300,
    ) -> None:
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least 1.")
        self._repository = repository
        self._lease_seconds = lease_seconds

    async def claim(
        self,
        *,
        notification_key: str,
        claimed_at: datetime | None = None,
    ) -> PlatformIntelligenceEscalationRetryClaim | None:
        if not isinstance(notification_key, str) or not notification_key.strip():
            raise ValueError("notification_key must be nonblank.")

        reference_at = claimed_at or datetime.now(timezone.utc)
        if reference_at.tzinfo is None or reference_at.utcoffset() is None:
            raise ValueError("claimed_at must be timezone-aware.")

        claim_token = str(uuid4())
        lease_expires_at = reference_at + timedelta(seconds=self._lease_seconds)

        claimed = await self._repository.claim_retry_candidate(
            notification_key=notification_key,
            claim_token=claim_token,
            claimed_at=reference_at,
            lease_expires_at=lease_expires_at,
        )

        if not claimed:
            return None

        return PlatformIntelligenceEscalationRetryClaim(
            notification_key=notification_key,
            claim_token=claim_token,
            claimed_at=reference_at,
            lease_expires_at=lease_expires_at,
            status=RetryCandidateClaimStatus.CLAIMED,
        )
