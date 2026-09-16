from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.routes.developer_admin_routes import router
from app.domain.identity.principal import Principal
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminLastAdminError,
    DeveloperAdminRecord,
    DeveloperAdminUserInactiveError,
    DeveloperAdminUserNotFoundError,
)


class FakeDeveloperAdminApiService:
    def __init__(self) -> None:
        self.administrators = [
            {
                "user_id": uuid4(),
                "email": "admin@example.com",
                "username": "admin",
                "status": "active",
                "email_verified": True,
            }
        ]

        self.grant_calls: list[UUID] = []
        self.revoke_calls: list[UUID] = []

        self.grant_actors: list[Principal] = []
        self.revoke_actors: list[Principal] = []

        self.grant_correlation_ids: list[str | None] = []
        self.revoke_correlation_ids: list[str | None] = []

        self.grant_error: Exception | None = None
        self.revoke_error: Exception | None = None

    async def list_developer_administrators(self):
        return [
            _record_from_dict(item)
            for item in self.administrators
        ]

    async def grant_developer_admin(
        self,
        *,
        user_id: UUID,
        actor: Principal,
        correlation_id: str | None = None,
    ):
        self.grant_calls.append(user_id)
        self.grant_actors.append(actor)
        self.grant_correlation_ids.append(correlation_id)

        if self.grant_error is not None:
            raise self.grant_error

        for item in self.administrators:
            if item["user_id"] == user_id:
                return _record_from_dict(item)

        record = {
            "user_id": user_id,
            "email": "target@example.com",
            "username": "target",
            "status": "active",
            "email_verified": True,
        }

        self.administrators.append(record)

        return _record_from_dict(record)

    async def revoke_developer_admin(
        self,
        *,
        user_id: UUID,
        actor: Principal,
        correlation_id: str | None = None,
    ):
        self.revoke_calls.append(user_id)
        self.revoke_actors.append(actor)
        self.revoke_correlation_ids.append(correlation_id)

        if self.revoke_error is not None:
            raise self.revoke_error


def _record_from_dict(item: dict) -> DeveloperAdminRecord:
    return DeveloperAdminRecord(
        user_id=item["user_id"],
        email=item["email"],
        username=item["username"],
        status=item["status"],
        email_verified=item["email_verified"],
    )


def _principal(*, roles: tuple[str, ...]) -> Principal:
    return Principal(
        user_id="operator-001",
        email="operator@example.com",
        email_verified=True,
        account_status="active",
        roles=roles,
    )


def _client(
    *,
    service: FakeDeveloperAdminApiService,
    roles: tuple[str, ...] = ("developer_admin",),
) -> TestClient:
    application = FastAPI()

    application.include_router(router)

    application.state.developer_admin_service = service

    async def override_current_principal() -> Principal:
        return _principal(roles=roles)

    application.dependency_overrides[get_current_principal] = (
        override_current_principal
    )

    return TestClient(application)


def test_list_developer_administrators_requires_permission() -> None:
    service = FakeDeveloperAdminApiService()

    with _client(
        service=service,
        roles=("beta_user",),
    ) as client:
        response = client.get(
            "/api/operations-center/developer-administrators"
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permission."


def test_list_developer_administrators_returns_contract() -> None:
    service = FakeDeveloperAdminApiService()

    with _client(service=service) as client:
        response = client.get(
            "/api/operations-center/developer-administrators"
        )

    assert response.status_code == 200

    body = response.json()

    assert len(body["administrators"]) == 1
    assert body["administrators"][0]["email"] == "admin@example.com"
    assert body["administrators"][0]["username"] == "admin"
    assert body["administrators"][0]["status"] == "active"
    assert body["administrators"][0]["email_verified"] is True


def test_grant_developer_admin_requires_permission() -> None:
    service = FakeDeveloperAdminApiService()
    target_user_id = uuid4()

    with _client(
        service=service,
        roles=("beta_user",),
    ) as client:
        response = client.post(
            "/api/operations-center/developer-administrators",
            json={"user_id": str(target_user_id)},
        )

    assert response.status_code == 403
    assert service.grant_calls == []
    assert service.grant_actors == []


def test_grant_developer_admin_returns_created_record() -> None:
    service = FakeDeveloperAdminApiService()
    target_user_id = uuid4()

    with _client(service=service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators",
            json={"user_id": str(target_user_id)},
        )

    assert response.status_code == 201

    body = response.json()

    assert body["user_id"] == str(target_user_id)
    assert body["email"] == "target@example.com"
    assert body["username"] == "target"
    assert body["status"] == "active"
    assert body["email_verified"] is True

    assert service.grant_calls == [target_user_id]

    assert len(service.grant_actors) == 1
    assert service.grant_actors[0].user_id == "operator-001"
    assert service.grant_actors[0].email == "operator@example.com"
    assert service.grant_actors[0].email_verified is True
    assert service.grant_actors[0].account_status == "active"


def test_grant_developer_admin_maps_missing_user_to_404() -> None:
    service = FakeDeveloperAdminApiService()

    service.grant_error = DeveloperAdminUserNotFoundError(
        "Target user does not exist."
    )

    with _client(service=service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators",
            json={"user_id": str(uuid4())},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Target user does not exist."


def test_grant_developer_admin_maps_inactive_user_to_409() -> None:
    service = FakeDeveloperAdminApiService()

    service.grant_error = DeveloperAdminUserInactiveError(
        "Developer Administrator privileges require an active, verified user."
    )

    with _client(service=service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators",
            json={"user_id": str(uuid4())},
        )

    assert response.status_code == 409
    assert "active, verified user" in response.json()["detail"]


def test_grant_developer_admin_rejects_invalid_uuid() -> None:
    service = FakeDeveloperAdminApiService()

    with _client(service=service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators",
            json={"user_id": "not-a-uuid"},
        )

    assert response.status_code == 422
    assert service.grant_calls == []
    assert service.grant_actors == []


def test_revoke_developer_admin_requires_permission() -> None:
    service = FakeDeveloperAdminApiService()
    target_user_id = uuid4()

    with _client(
        service=service,
        roles=("beta_user",),
    ) as client:
        response = client.delete(
            f"/api/operations-center/developer-administrators/{target_user_id}"
        )

    assert response.status_code == 403
    assert service.revoke_calls == []
    assert service.revoke_actors == []


def test_revoke_developer_admin_returns_no_content() -> None:
    service = FakeDeveloperAdminApiService()
    target_user_id = uuid4()

    with _client(service=service) as client:
        response = client.delete(
            f"/api/operations-center/developer-administrators/{target_user_id}"
        )

    assert response.status_code == 204
    assert response.content == b""
    assert service.revoke_calls == [target_user_id]

    assert len(service.revoke_actors) == 1
    assert service.revoke_actors[0].user_id == "operator-001"
    assert service.revoke_actors[0].email == "operator@example.com"
    assert service.revoke_actors[0].email_verified is True
    assert service.revoke_actors[0].account_status == "active"


def test_revoke_developer_admin_maps_missing_user_to_404() -> None:
    service = FakeDeveloperAdminApiService()

    service.revoke_error = DeveloperAdminUserNotFoundError(
        "Target user does not exist."
    )

    with _client(service=service) as client:
        response = client.delete(
            f"/api/operations-center/developer-administrators/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Target user does not exist."


def test_revoke_developer_admin_maps_last_admin_to_409() -> None:
    service = FakeDeveloperAdminApiService()

    service.revoke_error = DeveloperAdminLastAdminError(
        "The last Developer Administrator cannot be removed."
    )

    with _client(service=service) as client:
        response = client.delete(
            f"/api/operations-center/developer-administrators/{uuid4()}"
        )

    assert response.status_code == 409
    assert "last Developer Administrator" in response.json()["detail"]


def test_route_contract_is_stable() -> None:
    paths = {route.path for route in router.routes}

    assert (
        "/api/operations-center/developer-administrators"
        in paths
    )

    assert (
        "/api/operations-center/developer-administrators/{user_id}"
        in paths
    )