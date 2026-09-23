from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.application.operations_center.platform_intelligence_escalation_dispatch import (
    PlatformIntelligenceEscalationDispatchRequest,
)
from app.application.operations_center.platform_intelligence_escalation_retry_candidates import (
    PlatformIntelligenceEscalationRetryCandidate,
)
from app.application.operations_center.platform_intelligence_escalation_retry_execution import (
    PlatformIntelligenceEscalationRetryExecutionResult,
    PlatformIntelligenceEscalationRetryExecutionStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestration import (
    PlatformIntelligenceRetryRunStatus,
    PlatformIntelligenceRetryState,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestrator import (
    PlatformIntelligenceEscalationRetryOrchestrator,
)


REFERENCE = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)

NOTIFICATION_KEY = (
    "platform_intelligence_escalation:recommendation-1"
)


def dispatch_request() -> PlatformIntelligenceEscalationDispatchRequest:
    return PlatformIntelligenceEscalationDispatchRequest(
        recommendation_id="recommendation-1",
        risk_decision_id="decision-1",
        review_item_id="review-1",
        risk_level="HIGH",
        risk_score=0.82,
        quality_gate_status="PASSED",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        notification_key=NOTIFICATION_KEY,
        correlation_id="correlation-1",
        route="RISK_OWNER",
        reasons=("High risk level.",),
    )


def candidate() -> PlatformIntelligenceEscalationRetryCandidate:
    return PlatformIntelligenceEscalationRetryCandidate(
        notification_key=NOTIFICATION_KEY,
        recommendation_id="recommendation-1",
        risk_decision_id="decision-1",
        review_item_id="review-1",
        correlation_id="correlation-1",
        attempt=1,
        status="FAILED",
        updated_at=REFERENCE,
        error_code="PROVIDER_ERROR",
    )


class FakePolicy:
    def __init__(self, eligible: bool) -> None:
        self.eligible = eligible
        self.calls = 0

    async def evaluate(self, **kwargs):
        self.calls += 1
        return self.eligible


class FakeClaimService:
    def __init__(self, claim) -> None:
        self.claim_result = claim
        self.calls = 0

    async def claim(self, **kwargs):
        self.calls += 1
        return self.claim_result


class FakeStateReader:
    def __init__(self, state) -> None:
        self.state = state
        self.calls = 0

    async def get_retry_state(self, **kwargs):
        self.calls += 1
        return self.state


@dataclass(frozen=True)
class FakeClaim:
    token: str = "claim-token"


class FakeRetryExecution:
    def __init__(
        self,
        result: PlatformIntelligenceEscalationRetryExecutionResult,
    ) -> None:
        self.result = result
        self.calls = 0
        self.kwargs = None

    async def retry(self, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        return self.result


def valid_state() -> PlatformIntelligenceRetryState:
    return PlatformIntelligenceRetryState(
        notification_key=NOTIFICATION_KEY,
        recommendation_id="recommendation-1",
        recommendation_status="RECOMMENDED",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        quality_gate_status="PASSED",
        dispatch_request=dispatch_request(),
        email_request=object(),
    )


@pytest.mark.asyncio
async def test_not_policy_eligible_does_not_claim_or_execute() -> None:
    policy = FakePolicy(False)
    claims = FakeClaimService(FakeClaim())
    state = FakeStateReader(valid_state())

    execution = FakeRetryExecution(
        PlatformIntelligenceEscalationRetryExecutionResult(
            status=PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED,
            notification_key=NOTIFICATION_KEY,
            attempt=1,
            reason="SUCCEEDED",
        )
    )

    orchestrator = PlatformIntelligenceEscalationRetryOrchestrator(
        state_reader=state,
        policy_evaluator=policy,
        claim_service=claims,
        retry_execution=execution,
    )

    result = await orchestrator.run_candidate(
        candidate=candidate(),
        reference_at=REFERENCE,
    )

    assert result.status is PlatformIntelligenceRetryRunStatus.SKIPPED
    assert result.reason == "RETRY_POLICY_NOT_ELIGIBLE"
    assert claims.calls == 0
    assert state.calls == 0
    assert execution.calls == 0


@pytest.mark.asyncio
async def test_already_claimed_does_not_revalidate_or_execute() -> None:
    policy = FakePolicy(True)
    claims = FakeClaimService(None)
    state = FakeStateReader(valid_state())

    execution = FakeRetryExecution(
        PlatformIntelligenceEscalationRetryExecutionResult(
            status=PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED,
            notification_key=NOTIFICATION_KEY,
            attempt=1,
            reason="SUCCEEDED",
        )
    )

    orchestrator = PlatformIntelligenceEscalationRetryOrchestrator(
        state_reader=state,
        policy_evaluator=policy,
        claim_service=claims,
        retry_execution=execution,
    )

    result = await orchestrator.run_candidate(
        candidate=candidate(),
        reference_at=REFERENCE,
    )

    assert result.status is PlatformIntelligenceRetryRunStatus.SKIPPED
    assert result.reason == "RETRY_CANDIDATE_ALREADY_CLAIMED"
    assert state.calls == 0
    assert execution.calls == 0


@pytest.mark.asyncio
async def test_invalid_authoritative_state_blocks_execution() -> None:
    policy = FakePolicy(True)
    claims = FakeClaimService(FakeClaim())

    state = FakeStateReader(
        PlatformIntelligenceRetryState(
            notification_key=NOTIFICATION_KEY,
            recommendation_id="recommendation-1",
            recommendation_status="NOT_RECOMMENDED",
            review_status="IN_REVIEW",
            decision_status="PENDING_HUMAN_REVIEW",
            quality_gate_status="PASSED",
            dispatch_request=dispatch_request(),
            email_request=object(),
        )
    )

    execution = FakeRetryExecution(
        PlatformIntelligenceEscalationRetryExecutionResult(
            status=PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED,
            notification_key=NOTIFICATION_KEY,
            attempt=1,
            reason="SUCCEEDED",
        )
    )

    orchestrator = PlatformIntelligenceEscalationRetryOrchestrator(
        state_reader=state,
        policy_evaluator=policy,
        claim_service=claims,
        retry_execution=execution,
    )

    result = await orchestrator.run_candidate(
        candidate=candidate(),
        reference_at=REFERENCE,
    )

    assert result.status is PlatformIntelligenceRetryRunStatus.SKIPPED
    assert result.reason == "RECOMMENDATION_NO_LONGER_RECOMMENDED"
    assert execution.calls == 0


@pytest.mark.asyncio
async def test_valid_state_executes_after_claim() -> None:
    policy = FakePolicy(True)
    claims = FakeClaimService(FakeClaim())
    state = FakeStateReader(valid_state())

    execution = FakeRetryExecution(
        PlatformIntelligenceEscalationRetryExecutionResult(
            status=PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED,
            notification_key=NOTIFICATION_KEY,
            attempt=2,
            reason="RETRY_DISPATCHED",
            dispatch_result=type(
                "DispatchResult",
                (),
                {"provider_message_id": "provider-message-2"},
            )(),
        )
    )

    orchestrator = PlatformIntelligenceEscalationRetryOrchestrator(
        state_reader=state,
        policy_evaluator=policy,
        claim_service=claims,
        retry_execution=execution,
    )

    result = await orchestrator.run_candidate(
        candidate=candidate(),
        reference_at=REFERENCE,
    )

    assert result.status is PlatformIntelligenceRetryRunStatus.SUCCEEDED
    assert result.reason == "RETRY_DISPATCHED"
    assert result.attempt == 2
    assert result.provider_message_id == "provider-message-2"

    assert claims.calls == 1
    assert state.calls == 1
    assert execution.calls == 1

    assert execution.kwargs["request"] == dispatch_request()
    assert execution.kwargs["email_request"] is state.state.email_request
    assert execution.kwargs["reference_at"] == REFERENCE


@pytest.mark.asyncio
async def test_naive_reference_time_is_rejected() -> None:
    orchestrator = PlatformIntelligenceEscalationRetryOrchestrator(
        state_reader=FakeStateReader(valid_state()),
        policy_evaluator=FakePolicy(True),
        claim_service=FakeClaimService(FakeClaim()),
        retry_execution=FakeRetryExecution(
            PlatformIntelligenceEscalationRetryExecutionResult(
                status=PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED,
                notification_key=NOTIFICATION_KEY,
                attempt=1,
                reason="SUCCEEDED",
            )
        ),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        await orchestrator.run_candidate(
            candidate=candidate(),
            reference_at=datetime(2026, 9, 22, 12, 0),
        )


def test_candidate_contract_requires_correlation_id() -> None:
    with pytest.raises(TypeError, match="correlation_id"):
        PlatformIntelligenceEscalationRetryCandidate(
            notification_key=NOTIFICATION_KEY,
            recommendation_id="recommendation-1",
            risk_decision_id="decision-1",
            review_item_id="review-1",
            attempt=1,
            status="FAILED",
            updated_at=REFERENCE,
            error_code="PROVIDER_ERROR",
        )