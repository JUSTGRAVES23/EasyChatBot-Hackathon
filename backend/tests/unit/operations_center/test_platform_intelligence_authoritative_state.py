from datetime import datetime, timezone

import pytest

from app.application.operations_center.platform_intelligence_authoritative_state import (
    PlatformIntelligenceAuthoritativeState,
)


def make_state(**overrides):
    values = {
        "review_item_id": "REV-1",
        "risk_decision_id": "DEC-1",
        "risk_assessment_id": "ASSESS-1",
        "scope": "platform",
        "risk_level": "HIGH",
        "risk_score": 0.8,
        "priority": "HIGH",
        "review_status": "IN_REVIEW",
        "decision_status": "PENDING_HUMAN_REVIEW",
        "quality_gate_status": "PASSED",
        "evidence_references": ("E1",),
        "historical_references": ("H1",),
        "policy_id": "POLICY-1",
        "policy_version": "1.0",
        "created_at": datetime.now(timezone.utc),
        "recommendation_status": "RECOMMENDED",
        "recommendation_route": "RISK_OWNER",
        "recommendation_reasons": ("risk_level=HIGH",),
        "recommendation_id": "REC-1",
    }
    values.update(overrides)
    return PlatformIntelligenceAuthoritativeState(**values)


def test_valid_authoritative_state():
    state = make_state()
    assert state.review_item_id == "REV-1"
    assert state.recommendation_id == "REC-1"


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_risk_score_is_bounded(score):
    with pytest.raises(ValueError, match="risk_score"):
        make_state(risk_score=score)


def test_recommendation_id_requires_status():
    with pytest.raises(ValueError, match="recommendation_id"):
        make_state(
            recommendation_status=None,
            recommendation_id="REC-1",
        )
