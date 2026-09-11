from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.domain.identity.principal import (
    AccountStatus,
    Principal,
)
from app.project_control_center.api.project_control_router import (
    create_project_control_router,
)
from app.project_control_center.application.service import (
    ProjectControlService,
)
from app.project_control_center.domain.models import (
    ProjectDefinition,
    SourceSnapshot,
    SourceStatus,
    WorkstreamSnapshot,
    WorkstreamStatus,
)
from app.project_control_center.domain.ports import ProjectStatusSource
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)


@dataclass
class ApiTestSource(ProjectStatusSource):
    """
    Minimal authoritative-style source for API component tests.

    The source contains deterministic project-control data and has
    no external side effects.
    """

    @property
    def source_id(self) -> str:
        return "api-test"

    @property
    def source_name(self) -> str:
        return "API Test Source"

    def health(self) -> SourceSnapshot:
        return SourceSnapshot(
            source_id=self.source_id,
            name=self.source_name,
            status=SourceStatus.AVAILABLE,
            updated_at=datetime.now(timezone.utc),
        )

    def fetch_workstreams(
        self,
        project_id: str,
    ) -> list[WorkstreamSnapshot]:
        return [
            WorkstreamSnapshot(
                workstream_id="pcd",
                name="Project Control Center",
                completion_percent=85,
                status=WorkstreamStatus.HEALTHY,
                source=self.source_id,
            )
        ]

    def fetch_metrics(self, project_id: str):
        return []

    def fetch_issues(self, project_id: str):
        return []

    def fetch_risks(self, project_id: str):
        return []

    def fetch_actions(self, project_id: str):
        return []

    def fetch_milestones(self, project_id: str):
        return []


def make_project_control() -> ProjectControlService:
    """
    Build an isolated ProjectControlService for API tests.
    """

    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
        )
    )

    return ProjectControlService(
        registry=registry,
        sources=(ApiTestSource(),),
        snapshots=InMemorySnapshotRepository(),
    )


def make_principal(
    role: str = "operator",
) -> Principal:
    """
    Build an active, verified test principal.

    Authorization remains handled by the production
    AuthorizationService.
    """

    return Principal(
        user_id="test-user",
        email="test@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({role}),
    )


def make_identity_override(
    principal: Principal | None,
):
    """
    Override only the external identity/session resolution.

    This deliberately does NOT override authorization.

    Consequently:

        test Principal
            ↓
        real authorization dependency
            ↓
        real AuthorizationService
            ↓
        FUNCTIONALITY_CONTROL
    """

    async def override_get_current_principal() -> Principal:
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

        return principal

    return override_get_current_principal


def make_app(
    project_control: ProjectControlService,
    *,
    principal: Principal | None = None,
) -> FastAPI:
    """
    Build an isolated FastAPI application for API component tests.

    Only the identity lookup is overridden. The PCD authorization
    boundary remains production code.
    """

    application = FastAPI()

    application.include_router(
        create_project_control_router(
            project_control,
        )
    )

    application.dependency_overrides[
        get_current_principal
    ] = make_identity_override(principal)

    return application


def test_router_rejects_missing_project_control():
    with pytest.raises(
        ValueError,
        match="project_control cannot be None",
    ):
        create_project_control_router(
            None,  # type: ignore[arg-type]
        )


def test_unauthenticated_request_returns_401():
    application = make_app(
        make_project_control(),
        principal=None,
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Authentication required.",
    }


def test_beta_user_request_returns_403():
    application = make_app(
        make_project_control(),
        principal=make_principal("beta_user"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Insufficient permission.",
    }


def test_operator_request_returns_200():
    application = make_app(
        make_project_control(),
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 200


def test_admin_request_returns_200():
    application = make_app(
        make_project_control(),
        principal=make_principal("admin"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 200


def test_get_project_control_snapshot_returns_expected_contract():
    application = make_app(
        make_project_control(),
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 200

    body = response.json()

    assert body["project_id"] == "easychatbot"
    assert body["project_name"] == "EasyChatBot"
    assert body["project_status"] == "on_track"
    assert body["overall_progress_percent"] == 85.0
    assert body["release_readiness"] == "BETA READY"
    assert body["open_blockers"] == 0
    assert body["open_risks"] == 0

    assert body["workstreams"][0]["workstream_id"] == "pcd"
    assert body["workstreams"][0]["name"] == "Project Control Center"
    assert body["workstreams"][0]["status"] == "healthy"

    assert body["sources"][0]["source_id"] == "api-test"
    assert body["sources"][0]["status"] == "available"


def test_get_project_control_snapshot_does_not_persist():
    project_control = make_project_control()

    application = make_app(
        project_control,
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 200

    assert (
        project_control.snapshots.list_for_project(
            "easychatbot",
        )
        == []
    )


def test_unknown_project_returns_404():
    application = make_app(
        make_project_control(),
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/project-control/projects/missing",
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Unknown project: missing",
    }


def test_endpoint_is_get_only():
    application = make_app(
        make_project_control(),
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.post(
            "/project-control/projects/easychatbot",
        )

    assert response.status_code == 405


def test_endpoint_does_not_expose_agent_execution():
    application = make_app(
        make_project_control(),
        principal=make_principal("operator"),
    )

    openapi = application.openapi()
    paths = openapi["paths"]

    project_control_path = (
        "/project-control/projects/{project_id}"
    )

    assert project_control_path in paths

    assert "get" in paths[project_control_path]

    assert "post" not in paths[project_control_path]
    assert "put" not in paths[project_control_path]
    assert "patch" not in paths[project_control_path]
    assert "delete" not in paths[project_control_path]

    assert not any(
        "execute" in path.lower()
        for path in paths
        if "project-control" in path
    )