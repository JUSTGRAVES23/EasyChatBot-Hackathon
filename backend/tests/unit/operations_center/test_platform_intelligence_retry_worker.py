from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.operations_center.platform_intelligence_escalation_retry_candidates import (
    PlatformIntelligenceEscalationRetryCandidateBatch,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestration import (
    PlatformIntelligenceRetryRunResult,
    PlatformIntelligenceRetryRunStatus,
)
from app.application.operations_center.platform_intelligence_retry_worker import (
    PlatformIntelligenceRetryWorkerItemStatus,
    PlatformIntelligenceRetryWorkerRequest,
)
from app.application.operations_center.platform_intelligence_retry_worker_service import (
    PlatformIntelligenceRetryWorker,
)


REFERENCE = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)


class Candidate:
    def __init__(self, key: str, attempt: int = 1) -> None:
        self.notification_key = key
        self.recommendation_id = f"rec-{key}"
        self.attempt = attempt


class Discovery:
    def __init__(self, candidates) -> None:
        self.candidates = tuple(candidates)
        self.calls = 0
        self.limit = None

    async def discover(self, *, limit: int):
        self.calls += 1
        self.limit = limit
        return PlatformIntelligenceEscalationRetryCandidateBatch(
            candidates=self.candidates,
            limit=limit,
        )


class Orchestrator:
    def __init__(self, results=None, errors=None) -> None:
        self.results = results or {}
        self.errors = errors or {}
        self.calls = []

    async def run_candidate(self, *, candidate, reference_at):
        self.calls.append((candidate.notification_key, reference_at))
        if candidate.notification_key in self.errors:
            raise self.errors[candidate.notification_key]
        return self.results[candidate.notification_key]


def run_result(key, status, reason, attempt=1, provider=None):
    return PlatformIntelligenceRetryRunResult(
        notification_key=key,
        status=status,
        reason=reason,
        attempt=attempt,
        provider_message_id=provider,
    )


@pytest.mark.asyncio
async def test_empty_batch_is_a_noop():
    discovery = Discovery([])
    orchestrator = Orchestrator()

    worker = PlatformIntelligenceRetryWorker(
        discovery_service=discovery,
        orchestrator=orchestrator,
    )

    result = await worker.run(
        request=PlatformIntelligenceRetryWorkerRequest(limit=10),
        reference_at=REFERENCE,
    )

    assert result.discovered_count == 0
    assert result.processed_count == 0
    assert result.succeeded_count == 0
    assert result.skipped_count == 0
    assert result.failed_count == 0
    assert result.items == ()
    assert discovery.calls == 1
    assert discovery.limit == 10
    assert orchestrator.calls == []


@pytest.mark.asyncio
async def test_worker_processes_bounded_batch_and_preserves_results():
    candidates = [Candidate("key-a"), Candidate("key-b"), Candidate("key-c")]
    discovery = Discovery(candidates)
    orchestrator = Orchestrator(
        results={
            "key-a": run_result(
                "key-a",
                PlatformIntelligenceRetryRunStatus.SUCCEEDED,
                "RETRY_DISPATCHED",
                attempt=2,
                provider="provider-a",
            ),
            "key-b": run_result(
                "key-b",
                PlatformIntelligenceRetryRunStatus.SKIPPED,
                "RETRY_POLICY_NOT_ELIGIBLE",
            ),
            "key-c": run_result(
                "key-c",
                PlatformIntelligenceRetryRunStatus.FAILED,
                "DISPATCH_FAILED",
            ),
        }
    )

    worker = PlatformIntelligenceRetryWorker(
        discovery_service=discovery,
        orchestrator=orchestrator,
    )

    result = await worker.run(
        request=PlatformIntelligenceRetryWorkerRequest(limit=3),
        reference_at=REFERENCE,
    )

    assert result.discovered_count == 3
    assert result.processed_count == 3
    assert result.succeeded_count == 1
    assert result.skipped_count == 1
    assert result.failed_count == 1
    assert [item.notification_key for item in result.items] == [
        "key-a",
        "key-b",
        "key-c",
    ]
    assert result.items[0].status is PlatformIntelligenceRetryWorkerItemStatus.SUCCEEDED
    assert result.items[0].provider_message_id == "provider-a"
    assert result.items[1].status is PlatformIntelligenceRetryWorkerItemStatus.SKIPPED
    assert result.items[2].status is PlatformIntelligenceRetryWorkerItemStatus.FAILED
    assert orchestrator.calls == [
        ("key-a", REFERENCE),
        ("key-b", REFERENCE),
        ("key-c", REFERENCE),
    ]


@pytest.mark.asyncio
async def test_one_candidate_exception_does_not_abort_remaining_candidates():
    candidates = [Candidate("key-a"), Candidate("key-b"), Candidate("key-c")]
    discovery = Discovery(candidates)
    orchestrator = Orchestrator(
        results={
            "key-a": run_result(
                "key-a",
                PlatformIntelligenceRetryRunStatus.SUCCEEDED,
                "RETRY_DISPATCHED",
            ),
            "key-c": run_result(
                "key-c",
                PlatformIntelligenceRetryRunStatus.SKIPPED,
                "RETRY_CANDIDATE_ALREADY_CLAIMED",
            ),
        },
        errors={"key-b": RuntimeError("provider failure")},
    )

    worker = PlatformIntelligenceRetryWorker(
        discovery_service=discovery,
        orchestrator=orchestrator,
    )

    result = await worker.run(
        request=PlatformIntelligenceRetryWorkerRequest(limit=3),
        reference_at=REFERENCE,
    )

    assert result.processed_count == 3
    assert result.succeeded_count == 1
    assert result.skipped_count == 1
    assert result.failed_count == 1

    failed = result.items[1]
    assert failed.notification_key == "key-b"
    assert failed.reason == "CANDIDATE_EXECUTION_ERROR"
    assert failed.error_type == "RuntimeError"

    assert len(orchestrator.calls) == 3


@pytest.mark.asyncio
async def test_worker_rejects_naive_reference_time():
    worker = PlatformIntelligenceRetryWorker(
        discovery_service=Discovery([]),
        orchestrator=Orchestrator(),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        await worker.run(
            request=PlatformIntelligenceRetryWorkerRequest(limit=1),
            reference_at=datetime(2026, 9, 22, 12, 0),
        )


def test_worker_request_rejects_invalid_limit():
    with pytest.raises(ValueError, match="at least 1"):
        PlatformIntelligenceRetryWorkerRequest(limit=0)


def test_worker_result_rejects_duplicate_notification_keys():
    from app.application.operations_center.platform_intelligence_retry_worker import (
        PlatformIntelligenceRetryWorkerItemResult,
        PlatformIntelligenceRetryWorkerResult,
    )

    item = PlatformIntelligenceRetryWorkerItemResult(
        notification_key="duplicate",
        status=PlatformIntelligenceRetryWorkerItemStatus.SKIPPED,
        reason="SKIPPED",
        attempt=1,
    )

    with pytest.raises(ValueError, match="duplicate"):
        PlatformIntelligenceRetryWorkerResult(
            requested_limit=2,
            discovered_count=2,
            processed_count=2,
            succeeded_count=0,
            skipped_count=2,
            failed_count=0,
            items=(item, item),
        )
