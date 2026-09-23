from datetime import datetime, timezone

import pytest

from app.application.operations_center.platform_intelligence_authoritative_state import (
    PlatformIntelligenceAuthoritativeState,
)
from app.infrastructure.operations_center.platform_intelligence_authoritative_review_source import (
    PostgreSQLPlatformIntelligenceReviewSource,
)


class Repository:
    def __init__(self, state):
        self.state = state

    async def list_all(self):
        return (self.state,) if self.state else ()

    async def get(self, review_item_id):
        if self.state and self.state.review_item_id == review_item_id:
            return self.state
        return None

    async def get_by_recommendation_id(self, recommendation_id):
        if (
            self.state
            and self.state.recommendation_id == recommendation_id
        ):
            return self.state
        return None

    async def save(self, state):
        self.state = state


def state():
    return PlatformIntelligenceAuthoritativeState(
        review_item_id="REV-1",
        risk_decision_id="DEC-1",
        risk_assessment_id="ASSESS-1",
        scope="platform",
        risk_level="HIGH",
        risk_score=0.8,
        priority="HIGH",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        quality_gate_status="PASSED",
        evidence_references=("E1",),
        historical_references=("H1",),
        policy_id="POLICY-1",
        policy_version="1.0",
        created_at=datetime(2026, 9, 23, tzinfo=timezone.utc),
        rationale="Authoritative Platform Intelligence review requires human review.",
        recommendation_status="RECOMMENDED",
        recommendation_route="RISK_OWNER",
        recommendation_reasons=("risk",),
        recommendation_id="REC-1",
    )


@pytest.mark.asyncio
async def test_source_exposes_governed_projection():
    source = PostgreSQLPlatformIntelligenceReviewSource(
        Repository(state())
    )

    items = await source.list_reviews_async()

    assert len(items) == 1
    assert items[0]["review_item_id"] == "REV-1"
    assert items[0]["risk_decision_id"] == "DEC-1"
    assert items[0]["recommendation_id"] == "REC-1"
    assert (
        items[0]["rationale"]
        == "Authoritative Platform Intelligence review requires human review."
    )


@pytest.mark.asyncio
async def test_source_exposes_only_recommended_escalations():
    source = PostgreSQLPlatformIntelligenceReviewSource(
        Repository(state())
    )

    escalations = await source.list_escalations_async()

    assert len(escalations) == 1
    assert escalations[0]["recommendation_status"] == "RECOMMENDED"


@pytest.mark.asyncio
async def test_retry_state_is_rehydrated_from_authoritative_state():
    source = PostgreSQLPlatformIntelligenceReviewSource(
        Repository(state())
    )

    retry_state = await source.get_retry_state(
        "platform_intelligence_escalation:REC-1",
        "REC-1",
    )

    assert retry_state is not None
    assert retry_state.recommendation_id == "REC-1"
    assert retry_state.recommendation_status == "RECOMMENDED"
    assert retry_state.review_status == "IN_REVIEW"
    assert retry_state.decision_status == "PENDING_HUMAN_REVIEW"
    assert retry_state.quality_gate_status == "PASSED"
    assert (
        retry_state.email_request.rationale
        == "Authoritative Platform Intelligence review requires human review."
    )