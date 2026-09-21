from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.domain.identity.principal import Principal
from app.project_control_center.api.project_discovery_router import (
    create_project_discovery_router,
)
from app.project_control_center.application.project_discovery_service import (
    ProjectDiscoveryService,
)


class Repo:
    def __init__(self) -> None:
        self.items = {}

    def get(self, candidate_id):
        return self.items.get(candidate_id)

    def list_candidates(self):
        return list(self.items.values())

    def find_by_key(self, candidate_key):
        return next(
            (
                item
                for item in self.items.values()
                if item.candidate_key == candidate_key
            ),
            None,
        )

    def save(self, candidate):
        self.items[candidate.candidate_id] = candidate
        return candidate


class Registry:
    def create_project(self, **kwargs):
        from app.project_control_center.domain.models import ProjectDefinition

        return ProjectDefinition(**kwargs)


def _principal() -> Principal:
    """Return an active Developer Admin test principal.

    The isolated API test application keeps the production
    FUNCTIONALITY_CONTROL authorization dependency active. Only the
    identity lookup is overridden so the test does not require the
    production authentication repository in app.state.
    """
    return Principal(
        user_id="operator-001",
        email="operator@example.com",
        email_verified=True,
        account_status="active",
        roles=("developer_admin",),
    )


def client() -> TestClient:
    repository = Repo()
    registry = Registry()

    app = FastAPI()
    app.include_router(
        create_project_discovery_router(
            ProjectDiscoveryService(
                discovery_repository=repository,
                project_registry=registry,
            )
        )
    )

    async def override_current_principal() -> Principal:
        return _principal()

    # Override the actual identity dependency used by require_permission.
    # Do not replace require_permission itself: the API test must exercise
    # the real authorization path.
    app.dependency_overrides[get_current_principal] = (
        override_current_principal
    )

    return TestClient(app)


def test_create_and_list() -> None:
    test_client = client()

    response = test_client.post(
        "/project-control/discovery/candidates",
        json={
            "candidate_key": "x",
            "name": "X",
            "source": "internal",
        },
    )

    assert response.status_code == 201

    response = test_client.get(
        "/project-control/discovery/candidates"
    )

    assert response.status_code == 200
    assert response.json()[0]["candidate_key"] == "x"


def test_extra_fields_rejected() -> None:
    response = client().post(
        "/project-control/discovery/candidates",
        json={
            "candidate_key": "x",
            "name": "X",
            "source": "internal",
            "unexpected": True,
        },
    )

    assert response.status_code == 422


def test_unknown_returns_404() -> None:
    response = client().get(
        "/project-control/discovery/candidates/missing"
    )

    assert response.status_code == 404