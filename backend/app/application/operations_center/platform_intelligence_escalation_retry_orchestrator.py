"""Controlled orchestration for one PI escalation retry candidate."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.application.operations_center.platform_intelligence_escalation_retry_claim_service import (
    PlatformIntelligenceEscalationRetryClaimService,
)
from app.application.operations_center.platform_intelligence_escalation_retry_candidates import (
    PlatformIntelligenceEscalationRetryCandidate,
)
from app.application.operations_center.platform_intelligence_escalation_retry_execution import (
    PlatformIntelligenceEscalationRetryExecutionResult,
    PlatformIntelligenceEscalationRetryExecutionStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestration import (
    PlatformIntelligenceRetryRunResult,
    PlatformIntelligenceRetryRunStatus,
    PlatformIntelligenceRetryState,
)


class PlatformIntelligenceRetryStateReader(Protocol):
    async def get_retry_state(
        self,
        *,
        notification_key: str,
        recommendation_id: str,
    ) -> PlatformIntelligenceRetryState | None: ...


class PlatformIntelligenceRetryPolicyEvaluator(Protocol):
    async def evaluate(
        self,
        *,
        candidate: PlatformIntelligenceEscalationRetryCandidate,
        reference_at: datetime,
    ) -> bool: ...


class PlatformIntelligenceRetryExecutor(Protocol):
    async def retry(
        self,
        *,
        request: object,
        email_request: object,
        reference_at: datetime,
        claim_token: str,
    ) -> PlatformIntelligenceEscalationRetryExecutionResult: ...


class PlatformIntelligenceEscalationRetryOrchestrator:
    """Coordinates policy, durable claim, state revalidation and retry.

    This service deliberately does not discover candidates, implement retry
    policy, send email directly, or mutate human-review/risk state.

    The canonical retry execution service remains the owner of retry-policy
    enforcement and existing dispatch integration. The orchestrator only
    supplies the authoritative dispatch context after the durable claim and
    final state revalidation.
    """

    def __init__(
        self,
        *,
        state_reader: PlatformIntelligenceRetryStateReader,
        policy_evaluator: PlatformIntelligenceRetryPolicyEvaluator,
        claim_service: PlatformIntelligenceEscalationRetryClaimService,
        retry_execution: PlatformIntelligenceRetryExecutor,
    ) -> None:
        self._state_reader = state_reader
        self._policy_evaluator = policy_evaluator
        self._claim_service = claim_service
        self._retry_execution = retry_execution

    async def run_candidate(
        self,
        *,
        candidate: PlatformIntelligenceEscalationRetryCandidate,
        reference_at: datetime,
    ) -> PlatformIntelligenceRetryRunResult:
        if reference_at.tzinfo is None or reference_at.utcoffset() is None:
            raise ValueError("reference_at must be timezone-aware.")

        eligible = await self._policy_evaluator.evaluate(
            candidate=candidate,
            reference_at=reference_at,
        )
        if not eligible:
            return PlatformIntelligenceRetryRunResult(
                notification_key=candidate.notification_key,
                status=PlatformIntelligenceRetryRunStatus.SKIPPED,
                reason="RETRY_POLICY_NOT_ELIGIBLE",
                attempt=candidate.attempt,
            )

        claim = await self._claim_service.claim(
            notification_key=candidate.notification_key,
            claimed_at=reference_at,
        )
        if claim is None:
            return PlatformIntelligenceRetryRunResult(
                notification_key=candidate.notification_key,
                status=PlatformIntelligenceRetryRunStatus.SKIPPED,
                reason="RETRY_CANDIDATE_ALREADY_CLAIMED",
                attempt=candidate.attempt,
            )

        state = await self._state_reader.get_retry_state(
            notification_key=candidate.notification_key,
            recommendation_id=candidate.recommendation_id,
        )
        if state is None:
            return self._skipped(candidate, "AUTHORITATIVE_STATE_NOT_FOUND")
        if state.notification_key != candidate.notification_key:
            return self._skipped(candidate, "NOTIFICATION_KEY_MISMATCH")
        if state.recommendation_id != candidate.recommendation_id:
            return self._skipped(candidate, "RECOMMENDATION_ID_MISMATCH")
        if state.recommendation_status != "RECOMMENDED":
            return self._skipped(
                candidate, "RECOMMENDATION_NO_LONGER_RECOMMENDED"
            )
        if state.review_status != "IN_REVIEW":
            return self._skipped(candidate, "REVIEW_NOT_IN_REVIEW")
        if state.decision_status != "PENDING_HUMAN_REVIEW":
            return self._skipped(
                candidate, "DECISION_NO_LONGER_PENDING_HUMAN_REVIEW"
            )
        if state.quality_gate_status != "PASSED":
            return self._skipped(
                candidate, "QUALITY_GATE_NO_LONGER_PASSED"
            )

        execution = await self._retry_execution.retry(
            request=state.dispatch_request,
            email_request=state.email_request,
            reference_at=reference_at,
            claim_token=claim.claim_token,
        )

        if (
            execution.status
            is PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED
        ):
            dispatch_result = execution.dispatch_result

            dispatch_status = (
                getattr(
                    dispatch_result.status,
                    "value",
                    dispatch_result.status,
                )
                if dispatch_result is not None
                else None
            )

            if dispatch_status not in {"SENT", "IDEMPOTENT_REPLAY"}:
                return PlatformIntelligenceRetryRunResult(
                    notification_key=candidate.notification_key,
                    status=PlatformIntelligenceRetryRunStatus.FAILED,
                    reason=(
                        dispatch_result.error_code
                        if dispatch_result is not None
                        and dispatch_result.error_code
                        else "RETRY_DISPATCH_NOT_CONFIRMED_SUCCESS"
                    ),
                    attempt=execution.attempt,
                    provider_message_id=None,
                )

            return PlatformIntelligenceRetryRunResult(
                notification_key=candidate.notification_key,
                status=PlatformIntelligenceRetryRunStatus.SUCCEEDED,
                reason=execution.reason,
                attempt=execution.attempt,
                provider_message_id=(
                    dispatch_result.provider_message_id
                    if dispatch_result is not None
                    else None
                ),
            )

        if execution.status in (
            PlatformIntelligenceEscalationRetryExecutionStatus.NOT_ELIGIBLE,
            PlatformIntelligenceEscalationRetryExecutionStatus.NOT_DUE,
        ):
            return PlatformIntelligenceRetryRunResult(
                notification_key=candidate.notification_key,
                status=PlatformIntelligenceRetryRunStatus.SKIPPED,
                reason=execution.reason,
                attempt=execution.attempt,
            )

        return PlatformIntelligenceRetryRunResult(
            notification_key=candidate.notification_key,
            status=PlatformIntelligenceRetryRunStatus.FAILED,
            reason=execution.reason,
            attempt=execution.attempt,
        )

    @staticmethod
    def _skipped(
        candidate: PlatformIntelligenceEscalationRetryCandidate,
        reason: str,
    ) -> PlatformIntelligenceRetryRunResult:
        return PlatformIntelligenceRetryRunResult(
            notification_key=candidate.notification_key,
            status=PlatformIntelligenceRetryRunStatus.SKIPPED,
            reason=reason,
            attempt=candidate.attempt,
        )
