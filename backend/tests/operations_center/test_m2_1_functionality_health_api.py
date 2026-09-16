from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.operations_center import create_operations_center_router
from app.application.operations_center.dashboard_composition import OperationsCenterComposition


def client() -> TestClient:
    app = FastAPI()
    app.include_router(create_operations_center_router(composition=OperationsCenterComposition()))
    return TestClient(app)


def test_legacy_endpoint_defaults_to_adults() -> None:
    response = client().get("/api/operations-center/functionality-health")
    assert response.status_code == 200
    assert response.json()["environment"] == "adults"


def test_kids_environment() -> None:
    response = client().get("/api/operations-center/functionality-health?environment=kids")
    assert response.status_code == 200
    assert response.json()["environment"] == "kids"


def test_adults_environment() -> None:
    response = client().get("/api/operations-center/functionality-health?environment=adults")
    assert response.status_code == 200
    assert response.json()["environment"] == "adults"


def test_unknown_environment_is_rejected() -> None:
    response = client().get("/api/operations-center/functionality-health?environment=unknown")
    assert response.status_code == 422

