from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.routes.persistence_operations_routes import (
    create_persistence_operations_router,
)
from app.domain.identity.principal import AccountStatus, Principal


class FakePersistenceService:
    def snapshot(self, *, environment: str) -> dict[str, object]:
        return {
            "test": True,
            "operation": "snapshot",
            "environment": environment,
        }

    def health_snapshot(self, *, environment: str) -> dict[str, object]:
        return {
            "test": True,
            "operation": "health_snapshot",
            "environment": environment,
        }


def make_principal(role: str = "operator") -> Principal:
    return Principal(
        user_id="test-user",
        email="operator@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({role}),
    )


def make_identity_override(
    principal: Principal | None,
):
    async def override_get_current_principal() -> Principal:
        if principal is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

        return principal

    return override_get_current_principal


def make_app(
    *,
    principal: Principal | None,
) -> FastAPI:
    from app.api.dependencies.authorization import require_permission
    from app.domain.authorization.permissions import Permission

    application = FastAPI()

    application.include_router(
        create_persistence_operations_router(
            FakePersistenceService(),
            operator_dependency=require_permission(
                Permission.INTERNAL_DATA_READ,
            ),
        )
    )

    application.dependency_overrides[
        get_current_principal
    ] = make_identity_override(principal)

    return application


def test_unauthenticated_persistence_request_returns_401() -> None:
    application = make_app(principal=None)

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/persistence?environment=dev"
        )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication required."
    }


def test_operator_can_read_persistence_overview() -> None:
    application = make_app(
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/persistence?environment=dev"
        )

    assert response.status_code == 200
    assert response.json() == {
        "test": True,
        "operation": "snapshot",
        "environment": "dev",
    }


def test_operator_can_read_persistence_health() -> None:
    application = make_app(
        principal=make_principal("operator"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/persistence/health?environment=dev"
        )

    assert response.status_code == 200
    assert response.json() == {
        "test": True,
        "operation": "health_snapshot",
        "environment": "dev",
    }


def test_beta_user_cannot_read_persistence() -> None:
    application = make_app(
        principal=make_principal("beta_user"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/persistence?environment=dev"
        )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permission."
    }


def test_admin_can_read_persistence_health() -> None:
    application = make_app(
        principal=make_principal("admin"),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/operations-center/persistence/health?environment=dev"
        )

    assert response.status_code == 200
    assert response.json() == {
        "test": True,
        "operation": "health_snapshot",
        "environment": "dev",
    }