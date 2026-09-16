from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.privacy_screening import create_privacy_screening_router
from app.application.privacy.beta1_processing_catalog import create_beta1_processing_registry
from app.application.privacy.screening.adapter import ProcessingActivityScreeningAdapter
from app.application.privacy.screening.service import ScreeningService


def create_test_client() -> TestClient:
    registry = create_beta1_processing_registry()
    adapter = ProcessingActivityScreeningAdapter(ScreeningService())
    application = FastAPI()
    application.include_router(
        create_privacy_screening_router(
            processing_registry=registry,
            screening_adapter=adapter,
        )
    )
    return TestClient(application)


def test_get_processing_activities_uses_canonical_registry() -> None:
    response = create_test_client().get(
        "/api/privacy/screening/processing-activities"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["processing_id"] == "PA-BETA1-001"


def test_post_screen_invokes_m3_and_fails_closed() -> None:
    response = create_test_client().post(
        "/api/privacy/screening/screen",
        json={"processing_id": "PA-BETA1-001"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["processing_id"] == "PA-BETA1-001"
    assert body["status"] == "LEGAL_REVIEW_REQUIRED"
    assert {o["assessment"] for o in body["outcomes"]} == {"DPIA", "FRIA", "TIA"}


def test_unknown_processing_activity_is_rejected() -> None:
    response = create_test_client().post(
        "/api/privacy/screening/screen",
        json={"processing_id": "DOES-NOT-EXIST"},
    )
    assert response.status_code == 404


def test_browser_cannot_control_screening_criteria() -> None:
    response = create_test_client().post(
        "/api/privacy/screening/screen",
        json={
            "processing_id": "PA-BETA1-001",
            "criteria": [],
            "legal_materiality_established": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "LEGAL_REVIEW_REQUIRED"
