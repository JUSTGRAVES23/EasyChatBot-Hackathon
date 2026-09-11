from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.authorization import (
    require_permission,
)
from app.api.dependencies.identity import (
    get_current_principal,
)
from app.domain.authorization.permissions import (
    Permission,
)
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
)
from app.project_control_center.domain.ports import (
    ProjectStatusSource,
)
from app.project_control_center.infrastructure.in_memory import (
    InMemoryProjectRegistry,
    InMemorySnapshotRepository,
)


@dataclass
class AuthorizationTestSource(
    ProjectStatusSource,
):
    @property
    def source_id(self) -> str:
        return "authorization-test"

    @property
    def source_name(self) -> str:
        return "Authorization Test"

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
    ):
        return []

    def fetch_metrics(
        self,
        project_id: str,
    ):
        return []

    def fetch_issues(
        self,
        project_id: str,
    ):
        return []

    def fetch_risks(
        self,
        project_id: str,
    ):
        return []

    def fetch_actions(
        self,
        project_id: str,
    ):
        return []

    def fetch_milestones(
        self,
        project_id: str,
    ):
        return []


def make_project_control() -> ProjectControlService:
    registry = InMemoryProjectRegistry()

    registry.save(
        ProjectDefinition(
            project_id="easychatbot",
            name="EasyChatBot",
        )
    )

    return ProjectControlService(
        registry=registry,
        sources=(AuthorizationTestSource(),),
        snapshots=InMemorySnapshotRepository(),
    )


def make_router():
    return create_project_control_router(
        make_project_control(),
    )


def make_app() -> FastAPI:
    application = FastAPI()

    application.include_router(
        make_router(),
    )

    return application


def make_principal(
    *,
    roles: frozenset[str],
) -> Principal:
    return Principal(
        user_id="authorization-test-user",
        email="operator@example.test",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=roles,
    )


def test_beta_user_does_not_have_functionality_control_permission():
    principal = make_principal(
        roles=frozenset({"beta_user"}),
    )

    dependency = require_permission(
        Permission.FUNCTIONALITY_CONTROL,
    )

    application = FastAPI()

    @application.get("/test")
    async def protected(
        _: Principal = Depends(dependency),
    ):
        return {"ok": True}

    # Override the identity dependency, not the permission dependency.
    #
    # This preserves the real authorization path:
    #
    # get_current_principal
    #       -> require_permission(...)
    #       -> AuthorizationService
    #       -> PermissionDeniedError
    #       -> HTTP 403
    application.dependency_overrides[
        get_current_principal
    ] = lambda: principal

    with TestClient(application) as client:
        response = client.get("/test")

    assert response.status_code == 403


def test_operator_has_functionality_control_permission():
    principal = make_principal(
        roles=frozenset({"operator"}),
    )

    dependency = require_permission(
        Permission.FUNCTIONALITY_CONTROL,
    )

    application = FastAPI()

    @application.get("/test")
    async def protected(
        _: Principal = Depends(dependency),
    ):
        return {"ok": True}

    # Override only identity so that the real authorization
    # service evaluates the operator's permission.
    application.dependency_overrides[
        get_current_principal
    ] = lambda: principal

    with TestClient(application) as client:
        response = client.get("/test")

    assert response.status_code == 200


def test_project_control_router_uses_functionality_control_permission():
    router = make_router()

    routes = [
        route
        for route in router.routes
        if hasattr(route, "path")
        and route.path
        == "/project-control/projects/{project_id}"
    ]

    assert len(routes) == 1

    route = routes[0]

    assert route.methods == {"GET"}

    dependency_calls = {
        dependency.call
        for dependency in route.dependant.dependencies
    }

    assert len(dependency_calls) == 1

    permission_dependency = next(
        iter(dependency_calls)
    )

    assert permission_dependency is not None