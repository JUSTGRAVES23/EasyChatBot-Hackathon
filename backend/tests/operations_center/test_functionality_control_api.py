from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.operations_center import create_operations_center_router
from app.application.provider_management.functionality_operational_control_service import (
    OperationalControlResult,
)
from app.domain.identity.principal import (
    AccountStatus,
    Principal,
)


class FakeControlService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def stop(
        self,
        *,
        actor,
        actor_name: str,
        environment: str,
        functionality_id: str,
        reason: str,
    ) -> OperationalControlResult:
        self.calls.append(
            {
                "action": "stop",
                "actor": actor,
                "actor_name": actor_name,
                "environment": environment,
                "functionality_id": functionality_id,
                "reason": reason,
            }
        )

        return OperationalControlResult(
            functionality_id=functionality_id,
            environment=environment,
            availability="disabled",
            action="stop",
            reason=reason,
            changed_at=datetime.now(timezone.utc),
            changed_by=actor_name,
        )

    def resume(
        self,
        *,
        actor,
        actor_name: str,
        environment: str,
        functionality_id: str,
    ) -> OperationalControlResult:
        self.calls.append(
            {
                "action": "resume",
                "actor": actor,
                "actor_name": actor_name,
                "environment": environment,
                "functionality_id": functionality_id,
            }
        )

        return OperationalControlResult(
            functionality_id=functionality_id,
            environment=environment,
            availability="enabled",
            action="resume",
            reason=None,
            changed_at=datetime.now(timezone.utc),
            changed_by=actor_name,
        )


class FakeComposition:
    def __init__(self, control_service) -> None:
        self.dashboard_api = object()
        self.chat_operations_api = object()
        self.functionality_health_service = object()
        self.functionality_control_service = control_service
        self.event_service = object()
        self.provider_usage_dashboard_service = None


def make_principal(role: str) -> Principal:
    return Principal(
        user_id="test-user",
        email="test@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({role}),
    )


def create_test_app(
    *,
    principal: Principal | None,
    control_service=None,
) -> FastAPI:
    if control_service is None:
        control_service = FakeControlService()

    composition = FakeComposition(control_service)

    app = FastAPI()

    app.include_router(
        create_operations_center_router(
            composition=composition,
        )
    )

    async def override_principal() -> Principal:
        if principal is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )

        return principal

    app.dependency_overrides[get_current_principal] = override_principal

    return app


def test_operator_can_stop_functionality():
    control_service = FakeControlService()

    app = create_test_app(
        principal=make_principal("operator"),
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/conversation/stop",
            json={
                "environment": "kids",
                "reason": "Provider incident",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["functionality_id"] == "conversation"
    assert payload["environment"] == "kids"
    assert payload["availability"] == "disabled"
    assert payload["action"] == "stop"
    assert payload["reason"] == "Provider incident"

    assert len(control_service.calls) == 1


def test_admin_can_resume_functionality():
    control_service = FakeControlService()

    app = create_test_app(
        principal=make_principal("admin"),
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/telegram/resume",
            json={
                "environment": "adults",
            },
        )

    assert response.status_code == 200

    payload = response.json()

    assert payload["functionality_id"] == "telegram"
    assert payload["environment"] == "adults"
    assert payload["availability"] == "enabled"
    assert payload["action"] == "resume"

    assert len(control_service.calls) == 1


def test_beta_user_cannot_control_functionality():
    control_service = FakeControlService()

    app = create_test_app(
        principal=make_principal("beta_user"),
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/conversation/stop",
            json={
                "environment": "kids",
                "reason": "Unauthorized attempt",
            },
        )

    assert response.status_code == 403
    assert control_service.calls == []


def test_unauthenticated_user_cannot_control_functionality():
    control_service = FakeControlService()

    app = create_test_app(
        principal=None,
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/conversation/stop",
            json={
                "environment": "kids",
                "reason": "Attempt",
            },
        )

    assert response.status_code == 401
    assert control_service.calls == []


def test_unknown_functionality_is_rejected():
    class RejectingControlService(FakeControlService):
        def stop(self, **kwargs):
            raise ValueError(
                "Unknown functionality_id: not-real"
            )

    control_service = RejectingControlService()

    app = create_test_app(
        principal=make_principal("operator"),
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/not-real/stop",
            json={
                "environment": "kids",
                "reason": "Test",
            },
        )

    assert response.status_code == 400


def test_invalid_environment_is_rejected():
    control_service = FakeControlService()

    app = create_test_app(
        principal=make_principal("operator"),
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/conversation/stop",
            json={
                "environment": "production",
                "reason": "Test",
            },
        )

    assert response.status_code == 422
    assert control_service.calls == []


def test_empty_stop_reason_is_rejected():
    control_service = FakeControlService()

    app = create_test_app(
        principal=make_principal("operator"),
        control_service=control_service,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/conversation/stop",
            json={
                "environment": "kids",
                "reason": "",
            },
        )

    assert response.status_code == 422
    assert control_service.calls == []


def test_missing_control_service_returns_503():
    app = FastAPI()

    class NoControlComposition:
        dashboard_api = object()
        chat_operations_api = object()
        functionality_health_service = object()
        functionality_control_service = None
        event_service = object()
        provider_usage_dashboard_service = None

    app.include_router(
        create_operations_center_router(
            composition=NoControlComposition(),
        )
    )

    app.dependency_overrides[get_current_principal] = (
        lambda: make_principal("operator")
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/functionality/conversation/stop",
            json={
                "environment": "kids",
                "reason": "Test",
            },
        )

    assert response.status_code == 503

