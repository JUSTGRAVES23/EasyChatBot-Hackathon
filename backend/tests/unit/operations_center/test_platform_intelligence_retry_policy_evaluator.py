
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryRecord,
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_retry import (
    PlatformIntelligenceEscalationRetryDecision,
)
from app.application.operations_center.platform_intelligence_escalation_retry_candidates import (
    PlatformIntelligenceEscalationRetryCandidate,
)
from app.application.operations_center.platform_intelligence_retry_policy_evaluator import (
    PlatformIntelligenceRetryPolicyEvaluator,
)


def _candidate() -> PlatformIntelligenceEscalationRetryCandidate:
    now = datetime.now(timezone.utc)

    return PlatformIntelligenceEscalationRetryCandidate(
        notification_key="notification-1",
        recommendation_id="recommendation-1",
        risk_decision_id="decision-1",
        review_item_id="review-1",
        correlation_id="correlation-1",
        attempt=1,
        status=PlatformIntelligenceEscalationDeliveryStatus.FAILED,
        error_code="PROVIDER_ERROR",
        updated_at=now,
    )


def _record() -> PlatformIntelligenceEscalationDeliveryRecord:
    now = datetime.now(timezone.utc)

    return PlatformIntelligenceEscalationDeliveryRecord(
        notification_key="notification-1",
        recommendation_id="recommendation-1",
        risk_decision_id="decision-1",
        review_item_id="review-1",
        correlation_id="correlation-1",
        attempt=1,
        status=PlatformIntelligenceEscalationDeliveryStatus.FAILED,
        provider_message_id=None,
        error_code="PROVIDER_ERROR",
        created_at=now - timedelta(minutes=5),
        updated_at=now - timedelta(minutes=5),
    )


def _policy_result(
    decision: PlatformIntelligenceEscalationRetryDecision,
) -> SimpleNamespace:
    """Provide only the policy-result surface consumed by the adapter."""
    return SimpleNamespace(decision=decision)


@pytest.mark.asyncio
async def test_eligible_delivery_is_delegated_to_canonical_policy() -> None:
    repository = Mock()
    record = _record()
    repository.get_by_notification_key = AsyncMock(return_value=record)

    policy = Mock()
    policy.evaluate.return_value = _policy_result(
        PlatformIntelligenceEscalationRetryDecision.ELIGIBLE
    )

    evaluator = PlatformIntelligenceRetryPolicyEvaluator(
        delivery_repository=repository,
        retry_policy=policy,
    )

    reference_at = datetime.now(timezone.utc)

    result = await evaluator.evaluate(
        candidate=_candidate(),
        reference_at=reference_at,
    )

    assert result is True

    repository.get_by_notification_key.assert_awaited_once_with(
        "notification-1"
    )

    policy.evaluate.assert_called_once_with(
        record=record,
        reference_at=reference_at,
    )


@pytest.mark.asyncio
async def test_not_eligible_delivery_returns_false() -> None:
    repository = Mock()
    record = _record()
    repository.get_by_notification_key = AsyncMock(return_value=record)

    policy = Mock()
    policy.evaluate.return_value = _policy_result(
        PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
    )

    evaluator = PlatformIntelligenceRetryPolicyEvaluator(
        delivery_repository=repository,
        retry_policy=policy,
    )

    reference_at = datetime.now(timezone.utc)

    result = await evaluator.evaluate(
        candidate=_candidate(),
        reference_at=reference_at,
    )

    assert result is False

    repository.get_by_notification_key.assert_awaited_once_with(
        "notification-1"
    )

    policy.evaluate.assert_called_once_with(
        record=record,
        reference_at=reference_at,
    )


@pytest.mark.asyncio
async def test_missing_delivery_fails_closed() -> None:
    repository = Mock()
    repository.get_by_notification_key = AsyncMock(return_value=None)

    policy = Mock()

    evaluator = PlatformIntelligenceRetryPolicyEvaluator(
        delivery_repository=repository,
        retry_policy=policy,
    )

    result = await evaluator.evaluate(
        candidate=_candidate(),
        reference_at=datetime.now(timezone.utc),
    )

    assert result is False

    repository.get_by_notification_key.assert_awaited_once_with(
        "notification-1"
    )

    policy.evaluate.assert_not_called()


@pytest.mark.asyncio
async def test_candidate_notification_key_is_used_for_delivery_lookup() -> None:
    repository = Mock()
    repository.get_by_notification_key = AsyncMock(return_value=None)

    evaluator = PlatformIntelligenceRetryPolicyEvaluator(
        delivery_repository=repository,
        retry_policy=Mock(),
    )

    candidate = _candidate()

    await evaluator.evaluate(
        candidate=candidate,
        reference_at=datetime.now(timezone.utc),
    )

    repository.get_by_notification_key.assert_awaited_once_with(
        candidate.notification_key
    )


def test_constructor_rejects_missing_dependencies() -> None:
    with pytest.raises(ValueError, match="delivery_repository"):
        PlatformIntelligenceRetryPolicyEvaluator(
            delivery_repository=None,
            retry_policy=Mock(),
        )

    with pytest.raises(ValueError, match="retry_policy"):
        PlatformIntelligenceRetryPolicyEvaluator(
            delivery_repository=Mock(),
            retry_policy=None,
        )


@pytest.mark.asyncio
async def test_policy_result_is_not_reimplemented_by_adapter() -> None:
    repository = Mock()
    record = _record()
    repository.get_by_notification_key = AsyncMock(return_value=record)

    policy = Mock()
    policy.evaluate.return_value = _policy_result(
        PlatformIntelligenceEscalationRetryDecision.ELIGIBLE
    )

    evaluator = PlatformIntelligenceRetryPolicyEvaluator(
        delivery_repository=repository,
        retry_policy=policy,
    )

    reference_at = datetime.now(timezone.utc)

    result = await evaluator.evaluate(
        candidate=_candidate(),
        reference_at=reference_at,
    )

    assert result is True

    policy.evaluate.assert_called_once_with(
        record=record,
        reference_at=reference_at,
    )
