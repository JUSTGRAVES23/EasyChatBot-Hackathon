from types import SimpleNamespace

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.operations_center import create_operations_center_router
from app.application.operations_center.dashboard_composition import (
    create_operations_center_composition,
)


class Source:
    def _item(self):
        return SimpleNamespace(
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

    def list_reviews(self):
        return [self._item()]

    def get_review(self, review_item_id):
        return self._item() if review_item_id == "R1" else None

    def list_escalations(self):
        return [self._item()]


def _client(source=None, monkeypatch=None):
    app = FastAPI()
    if monkeypatch is not None:
        import app.api.operations_center as operations_center_module
        monkeypatch.setattr(
            operations_center_module,
            "require_permission",
            lambda _permission: (lambda: None),
        )
    composition = create_operations_center_composition(
        platform_intelligence_review_source=source
    )
    app.include_router(create_operations_center_router(composition=composition))
    return TestClient(app)


def test_existing_operations_center_dashboard_route_is_preserved(monkeypatch):
    client = _client(Source(), monkeypatch)
    response = client.get("/api/operations-center/dashboard")
    assert response.status_code == 200


def test_pi_reviews_are_exposed_through_existing_operations_center_router(monkeypatch):
    client = _client(Source(), monkeypatch)
    response = client.get("/api/operations-center/platform-intelligence/reviews")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_pi_escalations_are_exposed_through_existing_operations_center_router(monkeypatch):
    client = _client(Source(), monkeypatch)
    response = client.get("/api/operations-center/platform-intelligence/escalations")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_pi_review_detail_not_found_is_404(monkeypatch):
    client = _client(Source(), monkeypatch)
    response = client.get(
        "/api/operations-center/platform-intelligence/reviews/UNKNOWN"
    )
    assert response.status_code == 404


def test_pi_integration_fails_closed_when_source_is_not_configured(monkeypatch):
    client = _client(monkeypatch=monkeypatch)
    response = client.get("/api/operations-center/platform-intelligence/reviews")
    assert response.status_code == 503
