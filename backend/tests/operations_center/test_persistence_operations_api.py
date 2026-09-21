from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.persistence_operations_routes import (
    create_persistence_operations_router,
)


class FakeService:
    def snapshot(self, *, environment: str):
        return {"environment": environment, "kind": "snapshot"}

    def health_snapshot(self, *, environment: str):
        return {"environment": environment, "kind": "health"}


def make_client():
    app = FastAPI()

    def operator_dependency():
        return {"role": "operator"}

    app.include_router(
        create_persistence_operations_router(
            FakeService(),
            operator_dependency=operator_dependency,
        )
    )

    return TestClient(app)


def test_operator_can_read_overview_and_health():
    client = make_client()

    overview = client.get(
        "/api/operations-center/persistence?environment=dev"
    )
    health = client.get(
        "/api/operations-center/persistence/health?environment=staging"
    )

    assert overview.status_code == 200
    assert overview.json() == {
        "environment": "dev",
        "kind": "snapshot",
    }

    assert health.status_code == 200
    assert health.json() == {
        "environment": "staging",
        "kind": "health",
    }


def test_environment_contract_rejects_unknown_values():
    response = make_client().get(
        "/api/operations-center/persistence?environment=qa"
    )

    assert response.status_code == 422