from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.routes.developer_admin_routes import router
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminLastAdminError,
    DeveloperAdminRecord,
    DeveloperAdminUserInactiveError,
    DeveloperAdminUserNotFoundError,
)
from app.application.developer_admin.trusted_approval_provider import (
    TrustedApprovalRequest,
    TrustedApprovalUnavailableError,
)
from app.domain.identity.principal import Principal


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

    async def list_developer_administrators(self) -> list[DeveloperAdminRecord]:
        return [_record_from_dict(item) for item in self.administrators]


class FakeDeveloperAdminTransactionService:
    AUDIENCE = "easychatbot.developer_admin"
    GRANT_OPERATION = "developer_admin.grant"
    REVOKE_OPERATION = "developer_admin.revoke"

    def __init__(self) -> None:
        self.authorizations: dict[str, SimpleNamespace] = {}
        self.create_grant_calls: list[tuple[str, UUID]] = []
        self.create_revoke_calls: list[tuple[str, UUID]] = []
        self.approve_calls: list[tuple[str, str]] = []
        self.execute_grant_calls: list[tuple[str, str]] = []
        self.execute_revoke_calls: list[tuple[str, str]] = []

        self.grant_error: Exception | None = None
        self.revoke_error: Exception | None = None
        self.approve_error: Exception | None = None

    def create_grant_transaction(
        self,
        *,
        principal: Principal,
        target_user_id: UUID,
    ) -> SimpleNamespace:
        self.create_grant_calls.append((principal.user_id, target_user_id))
        authorization = self._new_authorization(
            principal=principal,
            target_user_id=target_user_id,
            operation=self.GRANT_OPERATION,
            risk_operation="grant",
        )
        self.authorizations[authorization.authorization_id] = authorization
        return authorization

    def create_revoke_transaction(
        self,
        *,
        principal: Principal,
        target_user_id: UUID,
    ) -> SimpleNamespace:
        self.create_revoke_calls.append((principal.user_id, target_user_id))
        authorization = self._new_authorization(
            principal=principal,
            target_user_id=target_user_id,
            operation=self.REVOKE_OPERATION,
            risk_operation="revoke",
        )
        self.authorizations[authorization.authorization_id] = authorization
        return authorization

    def get_authorization(
        self,
        *,
        authorization_id: str,
    ) -> SimpleNamespace | None:
        return self.authorizations.get(authorization_id)

    def attach_trusted_approval(
        self,
        *,
        principal: Principal,
        approval,
    ) -> SimpleNamespace:
        authorization = self.get_authorization(
            authorization_id=approval.authorization_id,
        )
        if authorization is None:
            raise ValueError("Transaction authorization was not found.")

        if self.approve_error is not None:
            raise self.approve_error

        self.approve_calls.append(
            (principal.user_id, approval.authorization_id)
        )
        authorization.state = SimpleNamespace(value="APPROVED")
        return authorization

    async def execute_grant(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        transaction,
    ):
        authorization = self.get_authorization(
            authorization_id=authorization_id,
        )
        if authorization is None:
            raise ValueError("Transaction authorization was not found.")

        self.execute_grant_calls.append(
            (principal.user_id, authorization_id)
        )

        if self.grant_error is not None:
            raise self.grant_error

        authorization.state = SimpleNamespace(value="CONSUMED")
        return SimpleNamespace(
            user_id=authorization.transaction.target_user_id,
        )

    async def execute_revoke(
        self,
        *,
        principal: Principal,
        authorization_id: str,
        transaction,
    ) -> None:
        authorization = self.get_authorization(
            authorization_id=authorization_id,
        )
        if authorization is None:
            raise ValueError("Transaction authorization was not found.")

        self.execute_revoke_calls.append(
            (principal.user_id, authorization_id)
        )

        if self.revoke_error is not None:
            raise self.revoke_error

        authorization.state = SimpleNamespace(value="CONSUMED")

    def _new_authorization(
        self,
        *,
        principal: Principal,
        target_user_id: UUID,
        operation: str,
        risk_operation: str,
    ) -> SimpleNamespace:
        created_at = datetime.now(timezone.utc)
        transaction = SimpleNamespace(
            transaction_id=str(uuid4()),
            principal_id=principal.user_id,
            operation=operation,
            risk_context={
                "target_user_id": str(target_user_id),
                "operation": risk_operation,
                "audience": self.AUDIENCE,
            },
            target_user_id=target_user_id,
        )
        return SimpleNamespace(
            authorization_id=str(uuid4()),
            transaction=transaction,
            state=SimpleNamespace(value="PENDING_USER_APPROVAL"),
            created_at=created_at,
            expires_at=created_at + timedelta(minutes=5),
        )


class FakeTrustedApprovalProvider:
    def __init__(self) -> None:
        self.calls: list[TrustedApprovalRequest] = []
        self.error: Exception | None = None

    async def approve(
        self,
        *,
        request: TrustedApprovalRequest,
    ):
        self.calls.append(request)

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            authorization_id=request.authorization_id,
            principal_id=request.principal_id,
            transaction_id=request.transaction_id,
            assurance_level="A2",
        )


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
    service: FakeDeveloperAdminApiService | None = None,
    transaction_service: FakeDeveloperAdminTransactionService | None = None,
    approval_provider: FakeTrustedApprovalProvider | None = None,
    roles: tuple[str, ...] = ("developer_admin",),
) -> TestClient:
    application = FastAPI()
    application.include_router(router)

    application.state.developer_admin_service = (
        service if service is not None else FakeDeveloperAdminApiService()
    )
    application.state.developer_admin_transaction_service = (
        transaction_service
        if transaction_service is not None
        else FakeDeveloperAdminTransactionService()
    )

    if approval_provider is not None:
        application.state.developer_admin_trusted_approval_provider = (
            approval_provider
        )

    async def override_current_principal() -> Principal:
        return _principal(roles=roles)

    application.dependency_overrides[get_current_principal] = (
        override_current_principal
    )

    return TestClient(application)


def test_list_developer_administrators_requires_permission() -> None:
    with _client(roles=("beta_user",)) as client:
        response = client.get(
            "/api/operations-center/developer-administrators"
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permission."


def test_list_developer_administrators_returns_contract() -> None:
    with _client() as client:
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


def test_grant_transaction_requires_permission() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    target_user_id = uuid4()

    with _client(
        transaction_service=transaction_service,
        roles=("beta_user",),
    ) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/grant",
            json={"target_user_id": str(target_user_id)},
        )

    assert response.status_code == 403
    assert transaction_service.create_grant_calls == []


def test_grant_transaction_returns_pending_authorization() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    target_user_id = uuid4()

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/grant",
            json={"target_user_id": str(target_user_id)},
        )

    assert response.status_code == 201
    body = response.json()

    assert body["operation"] == "developer_admin.grant"
    assert body["audience"] == "easychatbot.developer_admin"
    assert body["target_user_id"] == str(target_user_id)
    assert body["state"] == "PENDING_USER_APPROVAL"
    assert body["authorization_id"]
    assert body["transaction_id"]

    assert transaction_service.create_grant_calls == [
        ("operator-001", target_user_id)
    ]


def test_grant_transaction_rejects_invalid_uuid() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/grant",
            json={"target_user_id": "not-a-uuid"},
        )

    assert response.status_code == 422
    assert transaction_service.create_grant_calls == []


def test_grant_transaction_rejects_extra_fields() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/grant",
            json={
                "target_user_id": str(uuid4()),
                "operation": "developer_admin.revoke",
            },
        )

    assert response.status_code == 422
    assert transaction_service.create_grant_calls == []


def test_revoke_transaction_requires_permission() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    target_user_id = uuid4()

    with _client(
        transaction_service=transaction_service,
        roles=("beta_user",),
    ) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/revoke",
            json={"target_user_id": str(target_user_id)},
        )

    assert response.status_code == 403
    assert transaction_service.create_revoke_calls == []


def test_revoke_transaction_returns_pending_authorization() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    target_user_id = uuid4()

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/revoke",
            json={"target_user_id": str(target_user_id)},
        )

    assert response.status_code == 201
    body = response.json()

    assert body["operation"] == "developer_admin.revoke"
    assert body["audience"] == "easychatbot.developer_admin"
    assert body["target_user_id"] == str(target_user_id)
    assert body["state"] == "PENDING_USER_APPROVAL"

    assert transaction_service.create_revoke_calls == [
        ("operator-001", target_user_id)
    ]


def test_approve_transaction_requires_permission() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    provider = FakeTrustedApprovalProvider()

    with _client(
        transaction_service=transaction_service,
        approval_provider=provider,
        roles=("beta_user",),
    ) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/approve"
        )

    assert response.status_code == 403
    assert provider.calls == []
    assert transaction_service.approve_calls == []


def test_approve_transaction_delegates_to_trusted_provider() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    provider = FakeTrustedApprovalProvider()

    with _client(
        transaction_service=transaction_service,
        approval_provider=provider,
    ) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/approve"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["authorization_id"] == authorization.authorization_id
    assert body["transaction_id"] == authorization.transaction.transaction_id
    assert body["state"] == "APPROVED"

    assert len(provider.calls) == 1
    assert provider.calls[0].authorization_id == authorization.authorization_id
    assert provider.calls[0].principal_id == "operator-001"
    assert provider.calls[0].audience == "easychatbot.developer_admin"
    assert (
        provider.calls[0].transaction_id
        == authorization.transaction.transaction_id
    )

    assert transaction_service.approve_calls == [
        ("operator-001", authorization.authorization_id)
    ]


def test_approve_transaction_returns_503_when_provider_unavailable() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    provider = FakeTrustedApprovalProvider()
    provider.error = TrustedApprovalUnavailableError(
        "Trusted A2 approval provider is not configured."
    )

    with _client(
        transaction_service=transaction_service,
        approval_provider=provider,
    ) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/approve"
        )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Trusted A2 approval provider is not configured."
    )
    assert transaction_service.approve_calls == []


def test_approve_transaction_maps_unknown_authorization_to_404() -> None:
    provider = FakeTrustedApprovalProvider()

    with _client(approval_provider=provider) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/"
            f"{uuid4()}/approve"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Transaction authorization was not found."
    )
    assert provider.calls == []


def test_execute_transaction_requires_permission() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )

    with _client(
        transaction_service=transaction_service,
        roles=("beta_user",),
    ) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 403
    assert transaction_service.execute_grant_calls == []
    assert transaction_service.execute_revoke_calls == []


def test_execute_grant_transaction() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    target_user_id = uuid4()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=target_user_id,
    )

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["authorization_id"] == authorization.authorization_id
    assert body["state"] == "CONSUMED"
    assert transaction_service.execute_grant_calls == [
        ("operator-001", authorization.authorization_id)
    ]
    assert transaction_service.execute_revoke_calls == []


def test_execute_revoke_transaction() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    target_user_id = uuid4()
    authorization = transaction_service.create_revoke_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=target_user_id,
    )

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["authorization_id"] == authorization.authorization_id
    assert body["state"] == "CONSUMED"
    assert transaction_service.execute_revoke_calls == [
        ("operator-001", authorization.authorization_id)
    ]
    assert transaction_service.execute_grant_calls == []


def test_execute_transaction_maps_unknown_authorization_to_404() -> None:
    with _client() as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/"
            f"{uuid4()}/execute"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Transaction authorization was not found."
    )


def test_execute_transaction_maps_missing_user_to_404() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    transaction_service.grant_error = DeveloperAdminUserNotFoundError(
        "Target user does not exist."
    )

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Target user does not exist."


def test_execute_transaction_maps_inactive_user_to_409() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    transaction_service.grant_error = DeveloperAdminUserInactiveError(
        "Developer Administrator privileges require an active, verified user."
    )

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 409
    assert "active, verified user" in response.json()["detail"]


def test_execute_transaction_maps_last_admin_to_409() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_revoke_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    transaction_service.revoke_error = DeveloperAdminLastAdminError(
        "The last Developer Administrator cannot be removed."
    )

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 409
    assert "last Developer Administrator" in response.json()["detail"]


def test_execute_transaction_maps_permission_error_to_403() -> None:
    transaction_service = FakeDeveloperAdminTransactionService()
    authorization = transaction_service.create_grant_transaction(
        principal=_principal(roles=("developer_admin",)),
        target_user_id=uuid4(),
    )
    transaction_service.grant_error = PermissionError(
        "transaction authorization denied"
    )

    with _client(transaction_service=transaction_service) as client:
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/"
            f"{authorization.authorization_id}/execute"
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "transaction authorization denied"


def test_route_contract_is_transaction_based() -> None:
    paths = {route.path for route in router.routes}

    assert (
        "/api/operations-center/developer-administrators"
        in paths
    )
    assert (
        "/api/operations-center/developer-administrators/transactions/grant"
        in paths
    )
    assert (
        "/api/operations-center/developer-administrators/transactions/revoke"
        in paths
    )
    assert (
        "/api/operations-center/developer-administrators/transactions/"
        "{authorization_id}/approve"
        in paths
    )
    assert (
        "/api/operations-center/developer-administrators/transactions/"
        "{authorization_id}/execute"
        in paths
    )

    assert (
        "/api/operations-center/developer-administrators/{user_id}"
        not in paths
    )
