from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_dispatch import (
    PlatformIntelligenceEscalationDispatchRequest,
    PlatformIntelligenceEscalationDispatchService,
)


@dataclass
class DeliveryRecord:
    notification_key: str
    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    correlation_id: str
    attempt: int
    status: PlatformIntelligenceEscalationDeliveryStatus
    provider_message_id: str | None = None
    error_code: str | None = None


class FakeRepository:
    def __init__(self) -> None:
        self.records: dict[str, DeliveryRecord] = {}
        self.created = 0
        self.retries = 0
        self.succeeded = 0
        self.failed = 0

    async def get_by_notification_key(
        self,
        notification_key: str,
    ) -> DeliveryRecord | None:
        return self.records.get(notification_key)

    async def create_started(self, **kwargs) -> DeliveryRecord:
        self.created += 1

        record = DeliveryRecord(
            **kwargs,
            attempt=1,
            status=PlatformIntelligenceEscalationDeliveryStatus.STARTED,
        )

        self.records[kwargs["notification_key"]] = record
        return record

    async def mark_succeeded(
        self,
        *,
        notification_key: str,
        provider_message_id: str | None,
        claim_token: str | None = None,
    ) -> DeliveryRecord:
        self.succeeded += 1

        record = self.records[notification_key]
        record.status = PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        record.provider_message_id = provider_message_id

        return record

    async def mark_failed(
        self,
        *,
        notification_key: str,
        error_code: str,
        claim_token: str | None = None,
    ) -> DeliveryRecord:
        self.failed += 1

        record = self.records[notification_key]
        record.status = PlatformIntelligenceEscalationDeliveryStatus.FAILED
        record.error_code = error_code

        return record

    async def start_retry(
        self,
        *,
        notification_key: str,
        claim_token: str,
    ) -> DeliveryRecord:
        self.retries += 1

        record = self.records[notification_key]
        record.attempt += 1
        record.status = PlatformIntelligenceEscalationDeliveryStatus.STARTED

        return record


@dataclass
class WorkflowResult:
    delivery: object


class FakeWorkflow:
    def __init__(
        self,
        result=None,
        error: Exception | None = None,
    ) -> None:
        self.calls: list[object] = []
        self.result = result or {
            "provider_message_id": "resend-123",
        }
        self.error = error

    def send(self, request: object) -> WorkflowResult:
        self.calls.append(request)

        if self.error:
            raise self.error

        return WorkflowResult(delivery=self.result)


def make_request(
    **overrides,
) -> PlatformIntelligenceEscalationDispatchRequest:
    values = {
        "recommendation_id": "rec-1",
        "risk_decision_id": "risk-1",
        "review_item_id": "review-1",
        "risk_level": "HIGH",
        "risk_score": 0.82,
        "quality_gate_status": "PASSED",
        "review_status": "IN_REVIEW",
        "decision_status": "PENDING_HUMAN_REVIEW",
        "notification_key": (
            "platform_intelligence_escalation:rec-1"
        ),
        "correlation_id": "corr-1",
        "route": "RISK_OWNER",
        "reasons": ("High risk level.",),
    }

    values.update(overrides)

    return PlatformIntelligenceEscalationDispatchRequest(**values)


@pytest.mark.asyncio
async def test_dispatch_sends_and_persists_success():
    repo = FakeRepository()
    workflow = FakeWorkflow()

    service = PlatformIntelligenceEscalationDispatchService(
        delivery_repository=repo,
        email_workflow=workflow,
    )

    result = await service.dispatch(
        request=make_request(),
        email_request=object(),
    )

    assert result.status.value == "SENT"
    assert result.provider_message_id == "resend-123"
    assert repo.created == 1
    assert repo.succeeded == 1
    assert len(workflow.calls) == 1


@pytest.mark.asyncio
async def test_successful_delivery_is_terminal_idempotent_replay():
    repo = FakeRepository()
    workflow = FakeWorkflow()

    service = PlatformIntelligenceEscalationDispatchService(
        delivery_repository=repo,
        email_workflow=workflow,
    )

    first = await service.dispatch(
        request=make_request(),
        email_request=object(),
    )

    second = await service.dispatch(
        request=make_request(),
        email_request=object(),
    )

    assert first.status.value == "SENT"
    assert second.status.value == "IDEMPOTENT_REPLAY"
    assert second.provider_message_id == "resend-123"
    assert len(workflow.calls) == 1


@pytest.mark.asyncio
async def test_failed_delivery_is_retryable():
    repo = FakeRepository()

    failing = FakeWorkflow(
        error=RuntimeError("provider unavailable"),
    )

    service = PlatformIntelligenceEscalationDispatchService(
        delivery_repository=repo,
        email_workflow=failing,
    )

    first = await service.dispatch(
        request=make_request(),
        email_request=object(),
    )

    assert first.status.value == "FAILED"
    assert repo.failed == 1

    succeeding = FakeWorkflow()

    service = PlatformIntelligenceEscalationDispatchService(
        delivery_repository=repo,
        email_workflow=succeeding,
    )

    second = await service.dispatch(
        request=make_request(),
        email_request=object(),
        claim_token="test-claim-token",
    )

    assert second.status.value == "SENT"
    assert repo.retries == 1
    assert len(succeeding.calls) == 1


@pytest.mark.asyncio
async def test_invalid_state_is_blocked_before_repository_or_email():
    repo = FakeRepository()
    workflow = FakeWorkflow()

    service = PlatformIntelligenceEscalationDispatchService(
        delivery_repository=repo,
        email_workflow=workflow,
    )

    with pytest.raises(ValueError, match="quality gate"):
        await service.dispatch(
            request=make_request(
                quality_gate_status="FAILED",
            ),
            email_request=object(),
        )

    with pytest.raises(ValueError, match="review"):
        await service.dispatch(
            request=make_request(
                review_status="COMPLETED",
            ),
            email_request=object(),
        )

    with pytest.raises(ValueError, match="decision"):
        await service.dispatch(
            request=make_request(
                decision_status="ACCEPTED",
            ),
            email_request=object(),
        )

    assert repo.created == 0
    assert workflow.calls == []


def test_notification_key_is_recommendation_scoped():
    assert (
        PlatformIntelligenceEscalationDispatchService.build_notification_key(
            "rec-7",
        )
        == "platform_intelligence_escalation:rec-7"
    )


def test_notification_key_must_match_recommendation():
    valid_request = make_request()

    with pytest.raises(
        ValueError,
        match="notification_key",
    ):
        replace(
            valid_request,
            notification_key=(
                "platform_intelligence_escalation:other"
            ),
        )