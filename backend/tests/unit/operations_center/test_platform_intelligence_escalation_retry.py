
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry import (
    PlatformIntelligenceEscalationRetryDecision,
    PlatformIntelligenceEscalationRetryPolicy,
    PlatformIntelligenceEscalationRetryPolicyService,
    PlatformIntelligenceEscalationRetryPolicyStatus,
)


REFERENCE = datetime(
    2026,
    9,
    22,
    10,
    0,
    tzinfo=timezone.utc,
)


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
    created_at: datetime | None = REFERENCE
    updated_at: datetime | None = REFERENCE


def policy(**overrides):
    values = {
        "policy_id": "PI-RETRY",
        "policy_version": "1.0",
        "status": (
            PlatformIntelligenceEscalationRetryPolicyStatus
            .APPROVED
        ),
        "max_attempts": 4,
        "base_backoff_seconds": 60,
        "max_backoff_seconds": 300,
        "retryable_error_codes": frozenset(
            {
                "TIMEOUT",
                "CONNECTION_ERROR",
                "PROVIDER_ERROR",
            }
        ),
        "retry_interrupted_started": True,
    }

    values.update(overrides)

    return PlatformIntelligenceEscalationRetryPolicy(
        **values
    )


def record(
    *,
    status=PlatformIntelligenceEscalationDeliveryStatus.FAILED,
    attempt=1,
    error_code="PROVIDER_ERROR",
):
    return Record(
        notification_key=(
            "platform_intelligence_escalation:REC-1"
        ),
        recommendation_id="REC-1",
        risk_decision_id="DEC-1",
        review_item_id="REV-1",
        correlation_id="CORR-1",
        attempt=attempt,
        status=status,
        error_code=error_code,
        created_at=REFERENCE,
        updated_at=REFERENCE,
    )


def test_retryable_failed_delivery_is_eligible_with_deterministic_backoff():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(attempt=1),
        reference_at=REFERENCE + timedelta(seconds=60),
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.ELIGIBLE
    )

    assert result.backoff_seconds == 60

    assert result.next_eligible_at == (
        REFERENCE + timedelta(seconds=60)
    )

    assert result.policy_id == "PI-RETRY"
    assert result.policy_version == "1.0"


def test_failed_delivery_is_not_due_before_backoff():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(attempt=1),
        reference_at=REFERENCE + timedelta(seconds=59),
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    assert result.backoff_seconds == 60

    assert result.next_eligible_at == (
        REFERENCE + timedelta(seconds=60)
    )


def test_backoff_doubles_and_is_capped():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    assert service.backoff_seconds(attempt=1) == 60
    assert service.backoff_seconds(attempt=2) == 120
    assert service.backoff_seconds(attempt=3) == 240
    assert service.backoff_seconds(attempt=4) == 300
    assert service.backoff_seconds(attempt=10) == 300


def test_non_retryable_error_is_not_eligible():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(
            error_code="INVALID_RECIPIENT"
        ),
        reference_at=REFERENCE,
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    assert "not retryable" in result.reason


def test_missing_error_code_is_not_eligible():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(error_code=None),
        reference_at=REFERENCE,
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    assert "no error code" in result.reason


def test_maximum_attempts_is_enforced():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(attempt=4),
        reference_at=REFERENCE,
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    assert "Maximum delivery attempts" in result.reason


def test_draft_policy_cannot_authorize_retry():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy(
            status=(
                PlatformIntelligenceEscalationRetryPolicyStatus
                .DRAFT
            )
        )
    )

    result = service.evaluate(
        record=record(),
        reference_at=REFERENCE,
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    assert "not APPROVED" in result.reason


def test_interrupted_started_delivery_is_policy_controlled():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(
            status=(
                PlatformIntelligenceEscalationDeliveryStatus
                .STARTED
            ),
            attempt=1,
            error_code=None,
        ),
        reference_at=REFERENCE + timedelta(seconds=60),
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.ELIGIBLE
    )

    assert result.backoff_seconds == 60

    assert result.next_eligible_at == (
        REFERENCE + timedelta(seconds=60)
    )


def test_started_recovery_can_be_disabled_by_policy():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy(
            retry_interrupted_started=False
        )
    )

    result = service.evaluate(
        record=record(
            status=(
                PlatformIntelligenceEscalationDeliveryStatus
                .STARTED
            ),
            error_code=None,
        ),
        reference_at=REFERENCE + timedelta(seconds=60),
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )


def test_succeeded_delivery_is_never_retryable():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=record(
            status=(
                PlatformIntelligenceEscalationDeliveryStatus
                .SUCCEEDED
            ),
            error_code=None,
        ),
        reference_at=REFERENCE,
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )


def test_missing_delivery_timestamp_is_not_retryable():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    result = service.evaluate(
        record=Record(
            notification_key=(
                "platform_intelligence_escalation:REC-1"
            ),
            recommendation_id="REC-1",
            risk_decision_id="DEC-1",
            review_item_id="REV-1",
            correlation_id="CORR-1",
            attempt=1,
            status=(
                PlatformIntelligenceEscalationDeliveryStatus
                .FAILED
            ),
            error_code="PROVIDER_ERROR",
            created_at=None,
            updated_at=None,
        ),
        reference_at=REFERENCE,
    )

    assert (
        result.decision
        is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    assert "updated_at" in result.reason


def test_reference_time_must_be_timezone_aware():
    service = PlatformIntelligenceEscalationRetryPolicyService(
        policy=policy()
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        service.evaluate(
            record=record(),
            reference_at=datetime(
                2026,
                9,
                22,
                10,
                0,
            ),
        )


def test_policy_rejects_invalid_backoff_configuration():
    with pytest.raises(
        ValueError,
        match="max_backoff_seconds",
    ):
        policy(
            base_backoff_seconds=300,
            max_backoff_seconds=60,
        )


def test_policy_rejects_invalid_attempt_limit():
    with pytest.raises(
        ValueError,
        match="max_attempts",
    ):
        policy(
            max_attempts=0
        )

