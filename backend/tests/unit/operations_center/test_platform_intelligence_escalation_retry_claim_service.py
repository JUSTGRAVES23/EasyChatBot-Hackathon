from datetime import datetime, timedelta, timezone

import pytest

from app.application.operations_center.platform_intelligence_escalation_retry_claims import (
    RetryCandidateClaimStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_claim_service import (
    PlatformIntelligenceEscalationRetryClaimService,
)


class FakeClaimRepository:
    def __init__(self, result: bool) -> None:
        self.result = result
        self.calls = []

    async def claim_retry_candidate(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


@pytest.mark.asyncio
async def test_claim_returns_bounded_lease() -> None:
    repository = FakeClaimRepository(True)
    service = PlatformIntelligenceEscalationRetryClaimService(
        repository,
        lease_seconds=60,
    )
    reference = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)

    claim = await service.claim(
        notification_key="pi-key",
        claimed_at=reference,
    )

    assert claim is not None
    assert claim.notification_key == "pi-key"
    assert claim.claimed_at == reference
    assert claim.lease_expires_at == reference + timedelta(seconds=60)
    assert claim.status is RetryCandidateClaimStatus.CLAIMED
    assert repository.calls[0]["notification_key"] == "pi-key"


@pytest.mark.asyncio
async def test_claim_returns_none_when_candidate_is_already_claimed() -> None:
    repository = FakeClaimRepository(False)
    service = PlatformIntelligenceEscalationRetryClaimService(repository)

    claim = await service.claim(
        notification_key="pi-key",
        claimed_at=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
    )

    assert claim is None


@pytest.mark.asyncio
async def test_claim_rejects_naive_reference_time() -> None:
    repository = FakeClaimRepository(True)
    service = PlatformIntelligenceEscalationRetryClaimService(repository)

    with pytest.raises(ValueError, match="timezone-aware"):
        await service.claim(
            notification_key="pi-key",
            claimed_at=datetime(2026, 9, 22, 12, 0),
        )
