
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.authorization import require_permission
from app.api.dependencies.identity import get_current_principal
from app.api.operations_center_email_workflows import (
    create_email_workflows_router,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.principal import AccountStatus, Principal


class FakeScalarResult:
    """Minimal scalar result returned by the fake SQLAlchemy session."""

    def all(self):
        return []


class FakeSession:
    """
    Minimal read-only SQLAlchemy Session contract required by the
    PostgreSQL email workflow registry.
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def scalars(self, _statement):
        return FakeScalarResult()


class FakeSessionFactory:
    """Deterministic session factory for authorization tests."""

    def __call__(self):
        return FakeSession()


class FakeScheduler:
    """Minimal scheduler contract required by EmailWorkflowPortfolioService."""

    running = True

    def get_jobs(self):
        return []


class FakeSchedulerAdapter:
    scheduler = FakeScheduler()


class FakeSchedulerRuntime:
    scheduler_adapter = FakeSchedulerAdapter()


def make_principal(
    *,
    roles: frozenset[str],
) -> Principal:
    return Principal(
        user_id="email-workflow-authorization-test-user",
        email="operator@example.test",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=roles,
    )


def make_router():
    return create_email_workflows_router(
        session_factory=FakeSessionFactory(),
        operator_dependency=require_permission(
            Permission.INTERNAL_DATA_READ,
        ),
    )


def make_app(
    *,
    principal: Principal,
) -> FastAPI:
    application = FastAPI()

    application.state.scheduler_runtime = FakeSchedulerRuntime()

    application.include_router(
        make_router(),
    )

    # Override only the identity dependency.
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

    return application


def test_beta_user_cannot_read_email_workflows():
    application = make_app(
        principal=make_principal(
            roles=frozenset({"beta_user"}),
        ),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/email-workflows",
        )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permission.",
    }


def test_operator_can_read_email_workflows():
    application = make_app(
        principal=make_principal(
            roles=frozenset({"operator"}),
        ),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/email-workflows",
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["count"] == 0
    assert payload["workflows"] == []


def test_admin_can_read_email_workflows():
    application = make_app(
        principal=make_principal(
            roles=frozenset({"admin"}),
        ),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/email-workflows",
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["count"] == 0
    assert payload["workflows"] == []


def test_developer_admin_can_read_email_workflows():
    application = make_app(
        principal=make_principal(
            roles=frozenset({"developer_admin"}),
        ),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/email-workflows",
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ready"
    assert payload["count"] == 0
    assert payload["workflows"] == []


def test_email_workflow_router_protects_collection_endpoint():
    router = make_router()

    routes = [
        route
        for route in router.routes
        if hasattr(route, "path")
        and route.path
        == "/api/operations-center/email-workflows"
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


def test_email_workflow_router_protects_item_endpoint():
    router = make_router()

    routes = [
        route
        for route in router.routes
        if hasattr(route, "path")
        and route.path
        == "/api/operations-center/email-workflows/{workflow_id}"
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
