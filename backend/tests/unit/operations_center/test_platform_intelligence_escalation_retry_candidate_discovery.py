from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_candidate_discovery import (
    PlatformIntelligenceEscalationRetryCandidateDiscoveryService,
)

T1 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 22, 10, 1, tzinfo=timezone.utc)


@dataclass
class Record:
    notification_key: str
    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    correlation_id: str
    attempt: int
    status: PlatformIntelligenceEscalationDeliveryStatus
    provider_message_id: str | None = None
    error_code: str | None = None
    created_at: datetime | None = T1
    updated_at: datetime | None = T1


class Repository:
    def __init__(self, records):
        self.records = records
        self.limit = None

    async def list_retry_candidates(self, *, limit):
        self.limit = limit
        return self.records


@pytest.mark.asyncio
async def test_discovery_returns_only_failed_and_started_candidates():
    repository = Repository(
        [
            Record(
                "key-succeeded",
                "rec-s",
                "dec-s",
                "rev-s",
                "corr-s",
                1,
                PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED,
                updated_at=T1,
            ),
            Record(
                "key-failed",
                "rec-f",
                "dec-f",
                "rev-f",
                "corr-f",
                1,
                PlatformIntelligenceEscalationDeliveryStatus.FAILED,
                error_code="PROVIDER_ERROR",
                updated_at=T2,
            ),
            Record(
                "key-started",
                "rec-t",
                "dec-t",
                "rev-t",
                "corr-t",
                1,
                PlatformIntelligenceEscalationDeliveryStatus.STARTED,
                updated_at=T1,
            ),
        ]
    )

    service = PlatformIntelligenceEscalationRetryCandidateDiscoveryService(
        repository=repository
    )

    result = await service.discover(limit=50)

    assert repository.limit == 50
    assert [item.notification_key for item in result.candidates] == [
        "key-started",
        "key-failed",
    ]


@pytest.mark.asyncio
async def test_discovery_is_deterministically_ordered():
    repository = Repository(
        [
            Record(
                "key-b",
                "rec-b",
                "dec-b",
                "rev-b",
                "corr-b",
                1,
                PlatformIntelligenceEscalationDeliveryStatus.FAILED,
                updated_at=T1,
            ),
            Record(
                "key-a",
                "rec-a",
                "dec-a",
                "rev-a",
                "corr-a",
                1,
                PlatformIntelligenceEscalationDeliveryStatus.FAILED,
                updated_at=T1,
            ),
        ]
    )

    service = PlatformIntelligenceEscalationRetryCandidateDiscoveryService(
        repository=repository
    )

    result = await service.discover(limit=10)

    assert [item.notification_key for item in result.candidates] == [
        "key-a",
        "key-b",
    ]


@pytest.mark.asyncio
async def test_discovery_preserves_retry_metadata():
    repository = Repository(
        [
            Record(
                "key-1",
                "rec-1",
                "dec-1",
                "rev-1",
                "corr-1",
                2,
                PlatformIntelligenceEscalationDeliveryStatus.FAILED,
                error_code="TIMEOUT",
                updated_at=T2,
            )
        ]
    )

    service = PlatformIntelligenceEscalationRetryCandidateDiscoveryService(
        repository=repository
    )

    result = await service.discover(limit=10)
    candidate = result.candidates[0]

    assert candidate.attempt == 2
    assert candidate.error_code == "TIMEOUT"
    assert candidate.updated_at == T2
    assert candidate.status == "FAILED"


@pytest.mark.asyncio
async def test_discovery_rejects_invalid_limit():
    repository = Repository([])

    service = PlatformIntelligenceEscalationRetryCandidateDiscoveryService(
        repository=repository
    )

    with pytest.raises(ValueError, match="at least 1"):
        await service.discover(limit=0)
