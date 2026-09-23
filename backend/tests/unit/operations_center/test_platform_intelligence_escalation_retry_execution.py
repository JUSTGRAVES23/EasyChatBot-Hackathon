from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_dispatch import (
    PlatformIntelligenceEscalationDispatchRequest,
    PlatformIntelligenceEscalationDispatchResult,
    PlatformIntelligenceEscalationDispatchStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry import (
    PlatformIntelligenceEscalationRetryPolicy,
    PlatformIntelligenceEscalationRetryPolicyService,
    PlatformIntelligenceEscalationRetryPolicyStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry_execution import (
    PlatformIntelligenceEscalationRetryExecutionService,
    PlatformIntelligenceEscalationRetryExecutionStatus,
)


DELIVERY_TIME = datetime(
    2026,
    9,
    22,
    10,
    0,
    tzinfo=timezone.utc,
)

REFERENCE = datetime(
    2026,
    9,
    22,
    10,
    1,
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
    created_at: datetime | None = DELIVERY_TIME
    updated_at: datetime | None = DELIVERY_TIME


class Repository:
    def __init__(self, record):
        self.record = record
        self.retries = 0

    async def get_by_notification_key(self, key):
        if self.record is None:
            return None

        if self.record.notification_key == key:
            return self.record

        return None

    async def start_retry(self, *, notification_key):
        self.retries += 1

        self.record.attempt += 1
        self.record.status = (
            PlatformIntelligenceEscalationDeliveryStatus.STARTED
        )
        self.record.error_code = None
        self.record.updated_at = REFERENCE

        return self.record


class Dispatch:
    def __init__(self):
        self.calls = 0

    async def dispatch(self, *, request, email_request):
        self.calls += 1

        return PlatformIntelligenceEscalationDispatchResult(
            status=PlatformIntelligenceEscalationDispatchStatus.SENT,
            notification_key=request.notification_key,
            provider_message_id="provider-1",
            attempt=2,
        )


def policy():
    return PlatformIntelligenceEscalationRetryPolicyService(
        policy=PlatformIntelligenceEscalationRetryPolicy(
            policy_id="PI-RETRY",
            policy_version="1.0",
            status=(
                PlatformIntelligenceEscalationRetryPolicyStatus
                .APPROVED
            ),
            max_attempts=4,
            base_backoff_seconds=60,
            max_backoff_seconds=300,
            retryable_error_codes=frozenset(
                {"PROVIDER_ERROR"}
            ),
            retry_interrupted_started=True,
        )
    )


def request():
    return PlatformIntelligenceEscalationDispatchRequest(
        recommendation_id="REC-1",
        risk_decision_id="DEC-1",
        review_item_id="REV-1",
        risk_level="HIGH",
        risk_score=0.82,
        quality_gate_status="PASSED",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        notification_key=(
            "platform_intelligence_escalation:REC-1"
        ),
        correlation_id="CORR-1",
        route="RISK_OWNER",
        reasons=("High risk.",),
    )


def record(
    status,
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
        created_at=DELIVERY_TIME,
        updated_at=DELIVERY_TIME,
    )


@pytest.mark.asyncio
async def test_failed_delivery_retries_only_when_due():
    repository = Repository(
        record(
            PlatformIntelligenceEscalationDeliveryStatus.FAILED
        )
    )

    dispatch = Dispatch()

    service = PlatformIntelligenceEscalationRetryExecutionService(
        delivery_repository=repository,
        retry_policy=policy(),
        dispatch_service=dispatch,
    )

    early = await service.retry(
        request=request(),
        email_request=object(),
        reference_at=datetime(
            2026,
            9,
            22,
            10,
            0,
            30,
            tzinfo=timezone.utc,
        ),
    )

    assert (
        early.status
        is PlatformIntelligenceEscalationRetryExecutionStatus
        .NOT_DUE
    )

    assert repository.retries == 0
    assert dispatch.calls == 0

    due = await service.retry(
        request=request(),
        email_request=object(),
        reference_at=REFERENCE,
    )

    assert (
        due.status
        is PlatformIntelligenceEscalationRetryExecutionStatus
        .RETRIED
    )

    assert repository.retries == 1
    assert dispatch.calls == 1


@pytest.mark.asyncio
async def test_non_retryable_failure_does_not_dispatch():
    repository = Repository(
        record(
            PlatformIntelligenceEscalationDeliveryStatus.FAILED,
            error_code="INVALID_RECIPIENT",
        )
    )

    dispatch = Dispatch()

    service = PlatformIntelligenceEscalationRetryExecutionService(
        delivery_repository=repository,
        retry_policy=policy(),
        dispatch_service=dispatch,
    )

    result = await service.retry(
        request=request(),
        email_request=object(),
        reference_at=REFERENCE,
    )

    assert (
        result.status
        is PlatformIntelligenceEscalationRetryExecutionStatus
        .NOT_ELIGIBLE
    )

    assert repository.retries == 0
    assert dispatch.calls == 0


@pytest.mark.asyncio
async def test_started_recovery_does_not_increment_attempt():
    repository = Repository(
        record(
            PlatformIntelligenceEscalationDeliveryStatus.STARTED,
            error_code=None,
        )
    )

    dispatch = Dispatch()

    service = PlatformIntelligenceEscalationRetryExecutionService(
        delivery_repository=repository,
        retry_policy=policy(),
        dispatch_service=dispatch,
    )

    result = await service.retry(
        request=request(),
        email_request=object(),
        reference_at=REFERENCE,
    )

    assert (
        result.status
        is PlatformIntelligenceEscalationRetryExecutionStatus
        .RETRIED
    )

    assert repository.retries == 0
    assert repository.record.attempt == 1
    assert dispatch.calls == 1


@pytest.mark.asyncio
async def test_max_attempts_prevents_retry():
    repository = Repository(
        record(
            PlatformIntelligenceEscalationDeliveryStatus.FAILED,
            attempt=4,
        )
    )

    dispatch = Dispatch()

    service = PlatformIntelligenceEscalationRetryExecutionService(
        delivery_repository=repository,
        retry_policy=policy(),
        dispatch_service=dispatch,
    )

    result = await service.retry(
        request=request(),
        email_request=object(),
        reference_at=REFERENCE,
    )

    assert (
        result.status
        is PlatformIntelligenceEscalationRetryExecutionStatus
        .NOT_ELIGIBLE
    )

    assert repository.retries == 0
    assert dispatch.calls == 0


@pytest.mark.asyncio
async def test_retry_requires_existing_durable_record():
    repository = Repository(None)
    dispatch = Dispatch()

    service = PlatformIntelligenceEscalationRetryExecutionService(
        delivery_repository=repository,
        retry_policy=policy(),
        dispatch_service=dispatch,
    )

    with pytest.raises(
        ValueError,
        match="existing durable",
    ):
        await service.retry(
            request=request(),
            email_request=object(),
            reference_at=REFERENCE,
        )