from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.domain.identity.principal import Principal
from app.project_control_center.api.project_registry_router import (
    create_project_registry_router,
)
from app.project_control_center.application.project_registry_service import (
    ProjectRegistryService,
)
from app.project_control_center.domain.models import ProjectDefinition
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
)


def _principal() -> Principal:
    """Return an authorized test principal.

    The production router deliberately keeps FUNCTIONALITY_CONTROL
    authorization enabled. The isolated API test application therefore
    overrides only the identity lookup; it does not bypass the permission
    dependency itself.
    """
    return Principal(
        user_id="operator-001",
        email="operator@example.com",
        email_verified=True,
        account_status="active",
        roles=("developer_admin",),
    )


def _unauthorized_principal() -> Principal:
    """Return an authenticated principal without project-control rights.

    This is intentionally different from an unauthenticated principal.
    The test therefore verifies authorization rather than merely testing
    authentication.
    """
    return Principal(
        user_id="unauthorized-001",
        email="unauthorized@example.com",
        email_verified=True,
        account_status="active",
        roles=(),
    )


def _client() -> tuple[TestClient, InMemoryProjectRegistry]:
    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
            description="AI-powered language learning platform",
            owner="team",
            active=True,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )

    registry.save(
        ProjectDefinition(
            project_id="inactive-project",
            name="Inactive",
            active=False,
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    )

    app = FastAPI()

    app.include_router(
        create_project_registry_router(
            ProjectRegistryService(registry),
        )
    )

    async def override_current_principal() -> Principal:
        return _principal()

    # Keep the real require_permission() dependency active.
    #
    # Only the lower-level identity source is replaced so this isolated
    # test application does not need the production auth repository
    # in app.state.
    app.dependency_overrides[get_current_principal] = (
        override_current_principal
    )

    return TestClient(app), registry


def _unauthorized_client() -> TestClient:
    """Create an isolated client with an authenticated but unauthorized user."""

    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
            description="AI-powered language learning platform",
            owner="team",
            active=True,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )

    app = FastAPI()

    app.include_router(
        create_project_registry_router(
            ProjectRegistryService(registry),
        )
    )

    async def override_current_principal() -> Principal:
        return _unauthorized_principal()

    # Only replace identity resolution.
    #
    # The real authorization dependency remains active and must reject
    # this authenticated principal because it has no required permission.
    app.dependency_overrides[get_current_principal] = (
        override_current_principal
    )

    return TestClient(app)


def test_list_projects_returns_active_registry_projects() -> None:
    client, _ = _client()

    response = client.get(
        "/project-control/registry/projects"
    )

    assert response.status_code == 200

    assert [item["project_id"] for item in response.json()] == [
        "easychatbot"
    ]


def test_get_project_returns_registry_definition() -> None:
    client, _ = _client()

    response = client.get(
        "/project-control/registry/projects/easychatbot"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["project_id"] == "easychatbot"
    assert body["name"] == "EasyChatBot"
    assert body["description"] == (
        "AI-powered language learning platform"
    )


def test_get_unknown_project_returns_404() -> None:
    client, _ = _client()

    response = client.get(
        "/project-control/registry/projects/missing"
    )

    assert response.status_code == 404


def test_create_project_returns_201() -> None:
    client, registry = _client()

    response = client.post(
        "/project-control/registry/projects",
        json={
            "project_id": "new-project",
            "name": "New Project",
            "description": "Created through API",
            "owner": "owner",
        },
    )

    assert response.status_code == 201
    assert response.json()["project_id"] == "new-project"
    assert registry.get("new-project") is not None


def test_duplicate_project_returns_409() -> None:
    client, _ = _client()

    response = client.post(
        "/project-control/registry/projects",
        json={
            "project_id": "easychatbot",
            "name": "Duplicate",
        },
    )

    assert response.status_code == 409


def test_patch_project_updates_registry_definition() -> None:
    client, registry = _client()

    response = client.patch(
        "/project-control/registry/projects/easychatbot",
        json={
            "name": "EasyChatBot Updated",
            "active": False,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "EasyChatBot Updated"
    assert body["active"] is False

    updated_project = registry.get("easychatbot")

    assert updated_project is not None
    assert updated_project.active is False


def test_patch_empty_body_is_rejected() -> None:
    client, _ = _client()

    response = client.patch(
        "/project-control/registry/projects/easychatbot",
        json={},
    )

    assert response.status_code == 422


def test_malformed_create_payload_is_rejected() -> None:
    client, _ = _client()

    response = client.post(
        "/project-control/registry/projects",
        json={
            "project_id": "new-project",
            "name": "New Project",
            "unexpected": True,
        },
    )

    assert response.status_code == 422


def test_project_registry_requires_functionality_control() -> None:
    """Authenticated users without FUNCTIONALITY_CONTROL must be denied.

    This is intentionally a black-box authorization test.

    It verifies the security contract at the HTTP boundary rather than
    depending on FastAPI/Starlette's internal route representation.
    """
    client = _unauthorized_client()

    response = client.get(
        "/project-control/registry/projects"
    )

    assert response.status_code == 403