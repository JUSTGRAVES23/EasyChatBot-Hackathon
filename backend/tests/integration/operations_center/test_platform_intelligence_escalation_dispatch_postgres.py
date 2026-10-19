from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_dispatch import (
    PlatformIntelligenceEscalationDispatchRequest,
    PlatformIntelligenceEscalationDispatchService,
)
from app.infrastructure.operations_center.sqlalchemy_platform_intelligence_escalation_delivery_repository import (
    SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)


pytestmark = pytest.mark.asyncio


def _database_required() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests.")


class FakeEmailWorkflow:
    """Deterministic email-workflow double; no external provider is called."""

    def __init__(
        self,
        *,
        provider_message_id: str = "integration-provider-message-1",
        error: Exception | None = None,
    ) -> None:
        self.calls: list[object] = []
        self.provider_message_id = provider_message_id
        self.error = error

    async def send(self, request: object) -> dict[str, str]:
        self.calls.append(request)

        if self.error is not None:
            raise self.error

        return {
            "status": "accepted",
            "provider_message_id": self.provider_message_id,
        }


def _make_request(
    recommendation_id: str,
    *,
    correlation_id: str | None = None,
) -> PlatformIntelligenceEscalationDispatchRequest:
    return PlatformIntelligenceEscalationDispatchRequest(
        recommendation_id=recommendation_id,
        risk_decision_id=f"risk-{recommendation_id}",
        review_item_id=f"review-{recommendation_id}",
        risk_level="HIGH",
        risk_score=0.82,
        quality_gate_status="PASSED",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        notification_key=(
            "platform_intelligence_escalation:"
            f"{recommendation_id}"
        ),
        correlation_id=correlation_id or f"correlation-{recommendation_id}",
        route="RISK_OWNER",
        reasons=("High risk level.",),
    )


def _new_repository(engine):
    return SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
        create_async_session_factory(engine)
    )


async def _dispose(engine) -> None:
    await engine.dispose()


async def test_dispatch_persists_success_and_replays_after_new_service_instance() -> None:
    _database_required()

    recommendation_id = f"pi-e2e-replay-{uuid4()}"
    engine_one = create_async_database_engine()

    try:
        repository_one = _new_repository(engine_one)
        workflow_one = FakeEmailWorkflow(
            provider_message_id="provider-message-restart-safe",
        )
        service_one = PlatformIntelligenceEscalationDispatchService(
            delivery_repository=repository_one,
            email_workflow=workflow_one,
        )

        first = await service_one.dispatch(
            request=_make_request(recommendation_id),
            email_request=object(),
        )

        assert first.status.value == "SENT"
        assert first.provider_message_id == "provider-message-restart-safe"
        assert len(workflow_one.calls) == 1

        persisted = await repository_one.get_by_notification_key(
            first.notification_key
        )
        assert persisted is not None
        assert persisted.status is PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        assert persisted.attempt == 1
        assert persisted.provider_message_id == "provider-message-restart-safe"
    finally:
        await _dispose(engine_one)

    # Simulate a new application/repository instance after restart.
    engine_two = create_async_database_engine()

    try:
        repository_two = _new_repository(engine_two)
        workflow_two = FakeEmailWorkflow(
            provider_message_id="must-not-be-used",
        )
        service_two = PlatformIntelligenceEscalationDispatchService(
            delivery_repository=repository_two,
            email_workflow=workflow_two,
        )

        second = await service_two.dispatch(
            request=_make_request(recommendation_id),
            email_request=object(),
        )

        assert second.status.value == "IDEMPOTENT_REPLAY"
        assert second.provider_message_id == "provider-message-restart-safe"
        assert second.attempt == 1
        assert workflow_two.calls == []

        persisted_after_restart = (
            await repository_two.get_by_notification_key(
                second.notification_key
            )
        )
        assert persisted_after_restart is not None
        assert (
            persisted_after_restart.status
            is PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        )
        assert persisted_after_restart.attempt == 1
        assert (
            persisted_after_restart.provider_message_id
            == "provider-message-restart-safe"
        )
    finally:
        await _dispose(engine_two)


async def test_started_delivery_is_retried_after_service_restart() -> None:
    _database_required()

    recommendation_id = f"pi-e2e-started-retry-{uuid4()}"
    request = _make_request(recommendation_id)
    engine_one = create_async_database_engine()

    try:
        repository_one = _new_repository(engine_one)

        started = await repository_one.create_started(
            notification_key=request.notification_key,
            recommendation_id=request.recommendation_id,
            risk_decision_id=request.risk_decision_id,
            review_item_id=request.review_item_id,
            correlation_id=request.correlation_id,
        )

        assert started.status is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        assert started.attempt == 1
    finally:
        await _dispose(engine_one)

    # A STARTED record after restart has an ambiguous provider outcome.
    # Never automatically resend it; require explicit reconciliation.
    engine_two = create_async_database_engine()

    try:
        repository_two = _new_repository(engine_two)
        workflow_two = FakeEmailWorkflow(
            provider_message_id="provider-message-recovered",
        )
        service_two = PlatformIntelligenceEscalationDispatchService(
            delivery_repository=repository_two,
            email_workflow=workflow_two,
        )

        result = await service_two.dispatch(
            request=request,
            email_request=object(),
        )

        assert result.status.value == "FAILED"
        assert (
            getattr(result, "error_code", None)
            or getattr(result, "error", None)
            or getattr(result, "reason", None)
        ) in {
            "DELIVERY_OUTCOME_AMBIGUOUS_REQUIRES_RECONCILIATION",
            "RECONCILIATION_REQUIRED",
        }
        assert workflow_two.calls == []
        assert result.provider_message_id is None
        assert result.attempt == 1

        persisted = await repository_two.get_by_notification_key(
            request.notification_key
        )
        assert persisted is not None
        assert persisted.status is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        assert persisted.attempt == 1
        assert persisted.provider_message_id is None
    finally:
        await _dispose(engine_two)


async def test_duplicate_notification_key_is_protected_by_postgresql() -> None:
    _database_required()

    recommendation_id = f"pi-e2e-duplicate-{uuid4()}"
    notification_key = (
        "platform_intelligence_escalation:"
        f"{recommendation_id}"
    )
    engine = create_async_database_engine()

    async def create(repository):
        return await repository.create_started(
            notification_key=notification_key,
            recommendation_id=recommendation_id,
            risk_decision_id=f"risk-{recommendation_id}",
            review_item_id=f"review-{recommendation_id}",
            correlation_id=f"correlation-{recommendation_id}",
        )

    try:
        repository_one = _new_repository(engine)
        repository_two = _new_repository(engine)

        results = await asyncio.gather(
            create(repository_one),
            create(repository_two),
            return_exceptions=True,
        )

        successes = [result for result in results if not isinstance(result, Exception)]
        failures = [result for result in results if isinstance(result, Exception)]

        assert len(successes) == 1
        assert len(failures) == 1

        persisted = await repository_one.get_by_notification_key(
            notification_key
        )
        assert persisted is not None
        assert persisted.status is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        assert persisted.attempt == 1
    finally:
        await _dispose(engine)
