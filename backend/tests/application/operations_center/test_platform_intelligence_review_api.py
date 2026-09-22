from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.application.operations_center.platform_intelligence_review_api import (
    PlatformIntelligenceReviewAPI,
    PlatformIntelligenceReviewNotConfigured,
)
from app.application.operations_center.platform_intelligence_review_source import (
    PlatformIntelligenceReviewSource,
)


class FakeSource(PlatformIntelligenceReviewSource):
    def __init__(self, items):
        self.items = tuple(items)

    def list_reviews(self):
        return self.items

    def get_review(self, review_item_id):
        return next(
            (item for item in self.items if item.review_item_id == review_item_id),
            None,
        )

    def list_escalations(self):
        return tuple(
            item
            for item in self.items
            if getattr(
                getattr(item, "recommendation_status", None),
                "value",
                getattr(item, "recommendation_status", None),
            )
            == "RECOMMENDED"
        )


def projection(*, recommended=False):
    return SimpleNamespace(
        review_item_id="review-1",
        risk_decision_id="decision-1",
        risk_assessment_id="assessment-1",
        scope="platform",
        risk_level=SimpleNamespace(value="HIGH"),
        risk_score=0.8,
        priority=SimpleNamespace(value="HIGH"),
        review_status=SimpleNamespace(value="IN_REVIEW"),
        decision_status=SimpleNamespace(value="PENDING_HUMAN_REVIEW"),
        quality_gate_status=SimpleNamespace(value="PASSED"),
        evidence_references=("e1",),
        historical_references=("h1",),
        policy_id="risk-policy",
        policy_version="1.0",
        created_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
        assigned_reviewer="reviewer-1",
        assigned_at=datetime(2026, 9, 22, 1, tzinfo=timezone.utc),
        review_due_at=None,
        rationale="Governed review required.",
        recommendation_status=(
            SimpleNamespace(value="RECOMMENDED") if recommended else None
        ),
        recommendation_route=(
            SimpleNamespace(value="RISK_OWNER") if recommended else None
        ),
        recommendation_reasons=("risk_level=HIGH",) if recommended else (),
        recommendation_id="esc-1" if recommended else None,
        metadata={"sensitive": "must-not-leak"},
    )


def test_list_serializes_only_approved_projection_fields():
    api = PlatformIntelligenceReviewAPI(source=FakeSource([projection()]))

    result = api.list_reviews()

    assert result["status"] == "ready"
    assert result["count"] == 1
    assert result["items"][0]["risk_decision_id"] == "decision-1"
    assert "metadata" not in result["items"][0]


def test_get_missing_returns_none():
    api = PlatformIntelligenceReviewAPI(source=FakeSource([]))

    assert api.get_review("missing") is None


def test_escalations_only_include_recommended_items():
    api = PlatformIntelligenceReviewAPI(
        source=FakeSource([projection(), projection(recommended=True)])
    )

    result = api.list_escalations()

    assert result["count"] == 1
    assert result["items"][0]["recommendation_status"] == "RECOMMENDED"


def test_unconfigured_source_is_explicitly_not_configured():
    api = PlatformIntelligenceReviewAPI(source=None)

    with pytest.raises(PlatformIntelligenceReviewNotConfigured):
        api.list_reviews()

