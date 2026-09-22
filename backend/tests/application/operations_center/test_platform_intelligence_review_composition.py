from types import SimpleNamespace

from app.application.operations_center.dashboard_composition import (
    create_operations_center_composition,
)
from app.application.operations_center.platform_intelligence_review_api import (
    PlatformIntelligenceReviewAPI,
)


class Source:
    def list_reviews(self):
        return [
            SimpleNamespace(
                review_item_id="R1",
                risk_decision_id="D1",
                risk_assessment_id="A1",
                scope="platform",
                risk_level="HIGH",
                risk_score=0.8,
                priority="HIGH",
                review_status="PENDING",
                decision_status="PENDING_HUMAN_REVIEW",
                quality_gate_status="PASSED",
                evidence_references=("E1",),
                historical_references=("H1",),
                policy_id="P",
                policy_version="1",
                created_at=SimpleNamespace(
                    isoformat=lambda: "2026-09-22T00:00:00+00:00"
                ),
                assigned_reviewer=None,
                assigned_at=None,
                review_due_at=None,
                rationale="test",
                recommendation_status="RECOMMENDED",
                recommendation_route="HUMAN_REVIEW",
                recommendation_reasons=("risk",),
                recommendation_id="REC1",
            )
        ]

    def get_review(self, review_item_id):
        return (
            self.list_reviews()[0]
            if review_item_id == "R1"
            else None
        )

    def list_escalations(self):
        return self.list_reviews()


def test_operations_center_composition_exposes_pi_review_api():
    composition = create_operations_center_composition(
        platform_intelligence_review_source=Source()
    )

    assert isinstance(
        composition.platform_intelligence_review_api,
        PlatformIntelligenceReviewAPI,
    )

    assert (
        composition.platform_intelligence_review_api
        .list_reviews()["count"]
        == 1
    )


def test_operations_center_composition_default_is_fail_closed():
    composition = create_operations_center_composition()

    assert composition.platform_intelligence_review_api.configured is False