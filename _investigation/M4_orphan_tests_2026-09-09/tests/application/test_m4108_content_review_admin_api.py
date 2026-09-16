from __future__ import annotations

from fastapi.testclient import TestClient

from app.application.content_ingestion.review.admin_api import (
    create_admin_review_router,
)
from app.application.content_ingestion.review.models import (
    ReviewItem,
    ReviewOption,
)
from app.application.content_ingestion.review.queue import (
    AcademyContentReviewQueue,
)
from fastapi import FastAPI


def build_client():
    queue = AcademyContentReviewQueue()
    app = FastAPI()
    app.include_router(create_admin_review_router(queue))

    queue.submit(
        ReviewItem(
            review_id="review-1",
            content_id="content-1",
            source_id="lecture-130",
            source_text="Original source",
            content_type="question",
            question_text="Which strategy should be prioritised?",
            options=(
                ReviewOption("a", "Business hours"),
                ReviewOption("b", "Manual reviews"),
                ReviewOption("c", "Training"),
                ReviewOption("d", "Real-time analytics"),
            ),
            certification="ISC2 CGRC",
            exam_domain="Risk Management",
            sub_domain="Risk Assessment",
            topic="IAM / Access Control",
        )
    )

    return TestClient(app)


def test_pending_endpoint_returns_review_item():
    client = build_client()
    response = client.get("/api/admin/content-review/pending")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["review_id"] == "review-1"


def test_review_detail_contains_source_and_all_options():
    client = build_client()
    response = client.get("/api/admin/content-review/review-1")

    assert response.status_code == 200
    payload = response.json()

    assert payload["source_text"] == "Original source"
    assert len(payload["options"]) == 4
    assert payload["certification"] == "ISC2 CGRC"


def test_unknown_review_returns_404():
    client = build_client()

    response = client.get("/api/admin/content-review/not-found")

    assert response.status_code == 404


def test_pending_review_can_be_edited():
    client = build_client()

    response = client.patch(
        "/api/admin/content-review/review-1",
        json={"topic": "Access Control", "difficulty": "Intermediate"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["topic"] == "Access Control"
    assert payload["difficulty"] == "Intermediate"


def test_approval_requires_exactly_one_correct_option():
    client = build_client()

    response = client.post(
        "/api/admin/content-review/review-1/decision",
        json={
            "reviewer_id": "admin-1",
            "decision": "approve",
        },
    )

    assert response.status_code == 409


def test_approval_accepts_reviewer_selected_correct_answer():
    client = build_client()

    response = client.post(
        "/api/admin/content-review/review-1/decision",
        json={
            "reviewer_id": "admin-1",
            "decision": "approve",
            "options": [
                {"option_id": "a", "text": "Business hours", "is_correct": False},
                {"option_id": "b", "text": "Manual reviews", "is_correct": False},
                {"option_id": "c", "text": "Training", "is_correct": False},
                {"option_id": "d", "text": "Real-time analytics", "is_correct": True},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_rejection_is_available():
    client = build_client()

    response = client.post(
        "/api/admin/content-review/review-1/decision",
        json={
            "reviewer_id": "admin-1",
            "decision": "reject",
            "reviewer_note": "Source needs verification.",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_ui_template_exists():
    from pathlib import Path

    path = Path(
        "app/presentation/admin/content_review/review_page.html"
    )

    assert path.exists()
    text = path.read_text(encoding="utf-8")

    assert "Content Review Queue" in text
    assert "Approve" in text
    assert "Reject" in text
    assert "Original source" in text
