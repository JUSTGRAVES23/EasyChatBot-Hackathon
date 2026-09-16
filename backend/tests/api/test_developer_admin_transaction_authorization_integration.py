from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.identity import get_current_principal
from app.api.routes.developer_admin_routes import router
from app.application.authorization.authorization_service import AuthorizationService
from app.application.developer_admin.developer_admin_service import DeveloperAdminRecord
from app.application.developer_admin.developer_admin_transaction_service import (
    DeveloperAdminTransactionService,
)
from app.application.developer_admin.trusted_approval_provider import (
    TrustedApprovalRequest,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationService,
)
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceContext,
    AuthenticationAssuranceLevel,
)
from app.domain.identity.principal import AccountStatus, Principal
from app.domain.identity.transaction_authorization import (
    TransactionAuthorizationConsumer,
    TransactionAuthorizationRegistry,
    TrustedApprovalEvidence,
)


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


class FakeDeveloperAdminService:
    def __init__(self) -> None:
        self.grant_calls: list[UUID] = []
        self.revoke_calls: list[UUID] = []
        self.audit_events: list[str] = []

    async def list_developer_administrators(self):
        return ()

    async def grant_developer_admin(self, *, actor: Principal, user_id: UUID):
        self.grant_calls.append(user_id)
        self.audit_events.append("developer_admin.granted")
        return DeveloperAdminRecord(
            user_id=user_id,
            email="target@example.com",
            username="target",
            status="active",
            email_verified=True,
        )

    async def revoke_developer_admin(self, *, actor: Principal, user_id: UUID):
        self.revoke_calls.append(user_id)
        self.audit_events.append("developer_admin.revoked")


class FakeTrustedApprovalProvider:
    def __init__(self, clock: FixedClock) -> None:
        self.clock = clock
        self.level = AuthenticationAssuranceLevel.A2
        self.calls: list[TrustedApprovalRequest] = []

    async def approve(self, *, request: TrustedApprovalRequest):
        self.calls.append(request)
        context = AuthenticationAssuranceContext(
            principal_id=request.principal_id,
            assurance_level=self.level,
            authentication_time=self.clock.now(),
            assurance_time=self.clock.now(),
            authentication_method="test-mfa",
            authentication_strength="mfa",
            user_verified=True,
            phishing_resistant=self.level is AuthenticationAssuranceLevel.A3,
            issuer="easychatbot-test",
            subject=request.principal_id,
            audience=request.audience,
            evidence_id=f"evidence-{request.authorization_id}",
            policy_version="test-v1",
        )
        # Resolve the exact transaction from the application test harness.
        authorization = self.app.state.developer_admin_transaction_service.get_authorization(
            authorization_id=request.authorization_id
        )
        assert authorization is not None
        return TrustedApprovalEvidence(
            authorization_id=request.authorization_id,
            transaction=authorization.transaction,
            approved_at=self.clock.now(),
            evidence_id=f"approval-{request.authorization_id}",
            assurance_context=context,
        )


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)


def _principal(user_id: str = "operator-001") -> Principal:
    return Principal(
        user_id=user_id,
        email=f"{user_id}@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset({"developer_admin"}),
    )


def _app(now: datetime):
    clock = FixedClock(now)
    developer_admin_service = FakeDeveloperAdminService()
    registry = TransactionAuthorizationRegistry()
    transaction_authorization_service = TransactionAuthorizationApplicationService(
        authorization_service=AuthorizationService(),
        registry=registry,
        consumer=TransactionAuthorizationConsumer(registry),
    )
    transaction_service = DeveloperAdminTransactionService(
        developer_admin_service=developer_admin_service,
        transaction_authorization_service=transaction_authorization_service,
        clock=clock,
    )
    provider = FakeTrustedApprovalProvider(clock)

    application = FastAPI()
    application.include_router(router)
    application.state.developer_admin_service = developer_admin_service
    application.state.developer_admin_transaction_service = transaction_service
    application.state.developer_admin_trusted_approval_provider = provider
    application.state.current_principal = _principal()

    async def current_principal() -> Principal:
        return application.state.current_principal

    application.dependency_overrides[get_current_principal] = current_principal
    provider.app = application
    return application, clock, developer_admin_service, transaction_service, provider


def _create_grant(client: TestClient, target_user_id: UUID):
    response = client.post(
        "/api/operations-center/developer-administrators/transactions/grant",
        json={"target_user_id": str(target_user_id)},
    )
    assert response.status_code == 201
    return response.json()


def test_logged_in_developer_admin_alone_cannot_mutate(now: datetime) -> None:
    app, _, service, _, _ = _app(now)
    target = uuid4()
    with TestClient(app) as client:
        old_post = client.post(
            "/api/operations-center/developer-administrators",
            json={"user_id": str(target)},
        )
        old_delete = client.delete(
            f"/api/operations-center/developer-administrators/{target}"
        )
    assert old_post.status_code == 404
    assert old_delete.status_code == 404
    assert service.grant_calls == []
    assert service.revoke_calls == []


def test_no_transaction_means_no_mutation(now: datetime) -> None:
    app, _, service, _, _ = _app(now)
    with TestClient(app) as client:
        response = client.post(
            "/api/operations-center/developer-administrators/transactions/missing/execute"
        )
    assert response.status_code == 404
    assert service.grant_calls == []


def test_wrong_transaction_means_no_mutation(now: datetime) -> None:
    app, _, service, _, _ = _app(now)
    target_one = uuid4()
    target_two = uuid4()
    with TestClient(app) as client:
        first = _create_grant(client, target_one)
        second = _create_grant(client, target_two)
        approved = client.post(
            f"/api/operations-center/developer-administrators/transactions/{first['authorization_id']}/approve"
        )
        assert approved.status_code == 200
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/{second['authorization_id']}/execute"
        )
    assert response.status_code == 403
    assert service.grant_calls == []


def test_insufficient_assurance_means_no_mutation(now: datetime) -> None:
    app, _, service, transaction_service, provider = _app(now)
    provider.level = AuthenticationAssuranceLevel.A1
    target = uuid4()
    with TestClient(app) as client:
        created = _create_grant(client, target)
        approved = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/approve"
        )
        assert approved.status_code == 200
        executed = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/execute"
        )
    assert executed.status_code == 403
    assert service.grant_calls == []
    authorization = transaction_service.get_authorization(
        authorization_id=created["authorization_id"]
    )
    assert authorization is not None


def test_wrong_principal_means_no_mutation(now: datetime) -> None:
    app, _, service, _, _ = _app(now)
    target = uuid4()
    with TestClient(app) as client:
        created = _create_grant(client, target)
        approved = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/approve"
        )
        assert approved.status_code == 200
        app.state.current_principal = _principal("operator-002")
        executed = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/execute"
        )
    assert executed.status_code == 403
    assert service.grant_calls == []


def test_expired_transaction_means_no_mutation(now: datetime) -> None:
    app, clock, service, _, _ = _app(now)
    target = uuid4()
    with TestClient(app) as client:
        created = _create_grant(client, target)
        clock.value = now + timedelta(minutes=6)
        executed = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/execute"
        )
    assert executed.status_code == 403
    assert service.grant_calls == []


def test_successful_authorized_transaction_mutates_once_and_emits_audit(now: datetime) -> None:
    app, _, service, transaction_service, provider = _app(now)
    target = UUID("11111111-1111-4111-8111-111111111111")
    with TestClient(app) as client:
        created = _create_grant(client, target)
        approved = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/approve"
        )
        assert approved.status_code == 200
        executed = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/execute"
        )
        replay = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/execute"
        )
    assert executed.status_code == 200
    assert replay.status_code == 403
    assert service.grant_calls == [target]
    assert service.audit_events == ["developer_admin.granted"]
    assert len(provider.calls) == 1
    consumed = transaction_service.get_authorization(
        authorization_id=created["authorization_id"]
    )
    assert consumed is not None
    assert consumed.state.value == "CONSUMED"


def test_provider_unavailable_fails_closed_without_mutation(now: datetime) -> None:
    app, _, service, _, _ = _app(now)
    del app.state.developer_admin_trusted_approval_provider
    target = uuid4()
    with TestClient(app) as client:
        created = _create_grant(client, target)
        response = client.post(
            f"/api/operations-center/developer-administrators/transactions/{created['authorization_id']}/approve"
        )
    assert response.status_code == 503
    assert service.grant_calls == []
    assert service.audit_events == []
