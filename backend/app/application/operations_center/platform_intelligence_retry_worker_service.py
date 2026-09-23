"""Bounded, scheduler-free orchestration boundary for PI retry work."""

from __future__ import annotations

from datetime import datetime

from app.application.operations_center.platform_intelligence_escalation_retry_candidate_discovery import (
    PlatformIntelligenceEscalationRetryCandidateDiscoveryService,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestration import (
    PlatformIntelligenceRetryRunStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestrator import (
    PlatformIntelligenceEscalationRetryOrchestrator,
)
from app.application.operations_center.platform_intelligence_retry_worker import (
    PlatformIntelligenceRetryWorkerItemResult,
    PlatformIntelligenceRetryWorkerItemStatus,
    PlatformIntelligenceRetryWorkerRequest,
    PlatformIntelligenceRetryWorkerResult,
)


class PlatformIntelligenceRetryWorker:
    """Process one bounded candidate batch through the governed retry chain.

    This class deliberately does not:
    - schedule itself;
    - sleep;
    - create background tasks;
    - access providers;
    - implement retry policy;
    - claim candidates directly;
    - mutate risk or human-review state.

    The caller owns invocation timing and supplies the reference timestamp.
    """

    def __init__(
        self,
        *,
        discovery_service: PlatformIntelligenceEscalationRetryCandidateDiscoveryService,
        orchestrator: PlatformIntelligenceEscalationRetryOrchestrator,
    ) -> None:
        if discovery_service is None:
            raise ValueError("discovery_service cannot be None.")

        if orchestrator is None:
            raise ValueError("orchestrator cannot be None.")

        self._discovery_service = discovery_service
        self._orchestrator = orchestrator

    async def run(
        self,
        *,
        request: PlatformIntelligenceRetryWorkerRequest,
        reference_at: datetime,
    ) -> PlatformIntelligenceRetryWorkerResult:
        if reference_at.tzinfo is None or reference_at.utcoffset() is None:
            raise ValueError("reference_at must be timezone-aware.")

        batch = await self._discovery_service.discover(
            limit=request.limit,
        )

        results: list[PlatformIntelligenceRetryWorkerItemResult] = []

        for candidate in batch.candidates:
            try:
                execution = await self._orchestrator.run_candidate(
                    candidate=candidate,
                    reference_at=reference_at,
                )

            except Exception as exc:
                results.append(
                    PlatformIntelligenceRetryWorkerItemResult(
                        notification_key=candidate.notification_key,
                        status=(
                            PlatformIntelligenceRetryWorkerItemStatus
                            .FAILED
                        ),
                        reason="CANDIDATE_EXECUTION_ERROR",
                        attempt=candidate.attempt,
                        error_type=type(exc).__name__,
                    )
                )
                continue

            if (
                execution.status
                is PlatformIntelligenceRetryRunStatus.SUCCEEDED
            ):
                results.append(
                    PlatformIntelligenceRetryWorkerItemResult(
                        notification_key=execution.notification_key,
                        status=(
                            PlatformIntelligenceRetryWorkerItemStatus
                            .SUCCEEDED
                        ),
                        reason=execution.reason,
                        attempt=execution.attempt,
                        provider_message_id=(
                            execution.provider_message_id
                        ),
                    )
                )

            elif (
                execution.status
                is PlatformIntelligenceRetryRunStatus.SKIPPED
            ):
                results.append(
                    PlatformIntelligenceRetryWorkerItemResult(
                        notification_key=execution.notification_key,
                        status=(
                            PlatformIntelligenceRetryWorkerItemStatus
                            .SKIPPED
                        ),
                        reason=execution.reason,
                        attempt=execution.attempt,
                    )
                )

            else:
                results.append(
                    PlatformIntelligenceRetryWorkerItemResult(
                        notification_key=execution.notification_key,
                        status=(
                            PlatformIntelligenceRetryWorkerItemStatus
                            .FAILED
                        ),
                        reason=execution.reason,
                        attempt=execution.attempt,
                    )
                )

        succeeded = sum(
            item.status
            is PlatformIntelligenceRetryWorkerItemStatus.SUCCEEDED
            for item in results
        )

        skipped = sum(
            item.status
            is PlatformIntelligenceRetryWorkerItemStatus.SKIPPED
            for item in results
        )

        failed = sum(
            item.status
            is PlatformIntelligenceRetryWorkerItemStatus.FAILED
            for item in results
        )

        return PlatformIntelligenceRetryWorkerResult(
            requested_limit=request.limit,
            discovered_count=len(batch.candidates),
            processed_count=len(results),
            succeeded_count=succeeded,
            skipped_count=skipped,
            failed_count=failed,
            items=tuple(results),
        )