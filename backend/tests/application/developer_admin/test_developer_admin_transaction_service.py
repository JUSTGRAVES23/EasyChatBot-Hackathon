from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from app.application.authorization.authorization_service import (
    AuthorizationService,
)
from app.application.developer_admin.developer_admin_service import (
    DeveloperAdminRecord,
    DeveloperAdminService,
)
from app.application.developer_admin.developer_admin_transaction_service import (
    DeveloperAdminTransactionService,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationService,
    TransactionAuthorizationApplicationError,
)
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceContext,
    AuthenticationAssuranceLevel,
)
from app.domain.identity.principal import AccountStatus, Principal
from app.domain.identity.transaction_authorization import (
    CanonicalTransaction,
    TransactionAuthorizationConsumer,
    TransactionAuthorizationDecision,
    TransactionAuthorizationFailure,
    TransactionAuthorizationRegistry,
    TrustedApprovalEvidence,
    TransactionAuthorizationState,
)


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock(now: datetime) -> FixedClock:
    return FixedClock(now)


@pytest.fixture
def principal() -> Principal:
    return Principal(
        user_id="user-001",
        email="user-001@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(),
    )


@pytest.fixture
def target_user_id() -> UUID:
    return UUID("11111111-1111-4111-8111-111111111111")


@pytest.fixture
def different_target_user_id() -> UUID:
    return UUID("22222222-2222-4222-8222-222222222222")


@pytest.fixture
def developer_admin_service() -> Mock:
    service = Mock(spec=DeveloperAdminService)

    service.grant_developer_admin = AsyncMock(
        return_value=DeveloperAdminRecord(
            user_id=UUID("11111111-1111-4111-8111-111111111111"),
            email="target@example.com",
            username="target",
            status="active",
            email_verified=True,
        )
    )

    return service


@pytest.fixture
def transaction_authorization_service() -> (
    TransactionAuthorizationApplicationService
):
    registry = TransactionAuthorizationRegistry()

    return TransactionAuthorizationApplicationService(
        authorization_service=AuthorizationService(),
        registry=registry,
        consumer=TransactionAuthorizationConsumer(registry),
    )


@pytest.fixture
def service(
    developer_admin_service: Mock,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    clock: FixedClock,
) -> DeveloperAdminTransactionService:
    return DeveloperAdminTransactionService(
        developer_admin_service=developer_admin_service,
        transaction_authorization_service=transaction_authorization_service,
        clock=clock,
    )


def make_assurance_context(
    *,
    principal_id: str,
    now: datetime,
    level: AuthenticationAssuranceLevel = AuthenticationAssuranceLevel.A2,
) -> AuthenticationAssuranceContext:
    return AuthenticationAssuranceContext(
        principal_id=principal_id,
        assurance_level=level,
        authentication_time=now,
        assurance_time=now,
        authentication_method="test-mfa",
        authentication_strength="mfa",
        user_verified=True,
        phishing_resistant=(
            level is AuthenticationAssuranceLevel.A3
        ),
        issuer="easychatbot-test",
        subject=principal_id,
        audience="easychatbot.developer_admin",
        evidence_id="assurance-evidence-001",
        policy_version="test-policy-v1",
    )


def approve_transaction(
    *,
    transaction_authorization_service: (
        TransactionAuthorizationApplicationService
    ),
    authorization_id: str,
    transaction: CanonicalTransaction,
    principal: Principal,
    clock: FixedClock,
    level: AuthenticationAssuranceLevel = AuthenticationAssuranceLevel.A2,
):
    authorization = transaction_authorization_service.registry.get(
        authorization_id
    )

    assert authorization is not None
    assert (
        authorization.state
        is TransactionAuthorizationState.PENDING_USER_APPROVAL
    )

    approval = TrustedApprovalEvidence(
        authorization_id=authorization_id,
        transaction=transaction,
        approved_at=clock.now(),
        evidence_id=f"approval-{authorization_id}",
        assurance_context=make_assurance_context(
            principal_id=principal.user_id,
            now=clock.now(),
            level=level,
        ),
    )

    approved = transaction_authorization_service.attach_user_approval(
        principal=principal,
        authorization=authorization,
        approval=approval,
        clock=clock,
    )

    return approved


def test_create_grant_transaction_binds_exact_target(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    transaction = authorization.transaction

    assert (
        authorization.state
        is TransactionAuthorizationState.PENDING_USER_APPROVAL
    )
    assert transaction.principal_id == principal.user_id
    assert transaction.operation == "developer_admin.grant"

    risk_context = dict(transaction.risk_context)

    assert risk_context["target_user_id"] == str(target_user_id)
    assert risk_context["operation"] == "grant"
    assert risk_context["audience"] == service.AUDIENCE


def test_create_grant_transaction_uses_required_developer_admin_operation(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    assert authorization.transaction.operation == "developer_admin.grant"


def test_create_grant_transaction_requires_authenticated_principal(
    service: DeveloperAdminTransactionService,
    target_user_id: UUID,
    clock: FixedClock,
) -> None:
    inactive_principal = Principal(
        user_id="user-001",
        email="user-001@example.com",
        email_verified=False,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(),
    )

    with pytest.raises(Exception):
        service.create_grant_transaction(
            principal=inactive_principal,
            target_user_id=target_user_id,
            created_at=clock.now(),
            expires_at=clock.now() + timedelta(minutes=5),
        )


def test_target_user_id_is_extracted_from_canonical_transaction(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    different_target_user_id: UUID,
    clock: FixedClock,
) -> None:
    transaction = CanonicalTransaction.from_mapping(
        transaction_id=str(uuid4()),
        principal_id=principal.user_id,
        amount="0.00",
        currency="N/A",
        merchant_or_service="easychatbot",
        operation=service.GRANT_OPERATION,
        timestamp=clock.now(),
        nonce=str(uuid4()),
        risk_context={
            "target_user_id": str(different_target_user_id),
            "operation": "grant",
            "audience": service.AUDIENCE,
        },
    )

    extracted_target = service._target_user_id_from_transaction(
        transaction
    )

    assert extracted_target == different_target_user_id


def test_target_user_id_rejects_wrong_operation(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
) -> None:
    transaction = CanonicalTransaction.from_mapping(
        transaction_id=str(uuid4()),
        principal_id=principal.user_id,
        amount="0.00",
        currency="N/A",
        merchant_or_service="easychatbot",
        operation="developer_admin.revoke",
        timestamp=clock.now(),
        nonce=str(uuid4()),
        risk_context={
            "target_user_id": str(target_user_id),
            "operation": "grant",
            "audience": service.AUDIENCE,
        },
    )

    with pytest.raises(
        PermissionError,
        match="transaction operation is invalid",
    ):
        service._target_user_id_from_transaction(transaction)


def test_target_user_id_rejects_wrong_audience(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
) -> None:
    transaction = CanonicalTransaction.from_mapping(
        transaction_id=str(uuid4()),
        principal_id=principal.user_id,
        amount="0.00",
        currency="N/A",
        merchant_or_service="easychatbot",
        operation=service.GRANT_OPERATION,
        timestamp=clock.now(),
        nonce=str(uuid4()),
        risk_context={
            "target_user_id": str(target_user_id),
            "operation": "grant",
            "audience": "wrong.audience",
        },
    )

    with pytest.raises(
        PermissionError,
        match="transaction audience is invalid",
    ):
        service._target_user_id_from_transaction(transaction)


def test_target_user_id_rejects_missing_target(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    clock: FixedClock,
) -> None:
    transaction = CanonicalTransaction.from_mapping(
        transaction_id=str(uuid4()),
        principal_id=principal.user_id,
        amount="0.00",
        currency="N/A",
        merchant_or_service="easychatbot",
        operation=service.GRANT_OPERATION,
        timestamp=clock.now(),
        nonce=str(uuid4()),
        risk_context={
            "operation": "grant",
            "audience": service.AUDIENCE,
        },
    )

    with pytest.raises(
        PermissionError,
        match="transaction target is invalid",
    ):
        service._target_user_id_from_transaction(transaction)


def test_target_user_id_rejects_invalid_uuid(
    service: DeveloperAdminTransactionService,
    principal: Principal,
    clock: FixedClock,
) -> None:
    transaction = CanonicalTransaction.from_mapping(
        transaction_id=str(uuid4()),
        principal_id=principal.user_id,
        amount="0.00",
        currency="N/A",
        merchant_or_service="easychatbot",
        operation=service.GRANT_OPERATION,
        timestamp=clock.now(),
        nonce=str(uuid4()),
        risk_context={
            "target_user_id": "not-a-uuid",
            "operation": "grant",
            "audience": service.AUDIENCE,
        },
    )

    with pytest.raises(
        PermissionError,
        match="transaction target is invalid",
    ):
        service._target_user_id_from_transaction(transaction)


@pytest.mark.asyncio
async def test_execute_grant_requires_a2_assurance(
    service: DeveloperAdminTransactionService,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
    developer_admin_service: Mock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    approve_transaction(
        transaction_authorization_service=transaction_authorization_service,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        principal=principal,
        clock=clock,
        level=AuthenticationAssuranceLevel.A1,
    )

    with pytest.raises(
        PermissionError,
        match="transaction authorization denied",
    ):
        await service.execute_grant(
            principal=principal,
            authorization_id=authorization.authorization_id,
            transaction=authorization.transaction,
            clock=clock,
        )

    developer_admin_service.grant_developer_admin.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_grant_allows_exact_authorized_transaction(
    service: DeveloperAdminTransactionService,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
    developer_admin_service: Mock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    approve_transaction(
        transaction_authorization_service=transaction_authorization_service,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        principal=principal,
        clock=clock,
        level=AuthenticationAssuranceLevel.A2,
    )

    result = await service.execute_grant(
        principal=principal,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        clock=clock,
    )

    assert result.user_id == target_user_id

    developer_admin_service.grant_developer_admin.assert_awaited_once_with(
        actor=principal,
        user_id=target_user_id,
    )


@pytest.mark.asyncio
async def test_execute_grant_cannot_reuse_consumed_authorization(
    service: DeveloperAdminTransactionService,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
    developer_admin_service: Mock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    approve_transaction(
        transaction_authorization_service=transaction_authorization_service,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        principal=principal,
        clock=clock,
    )

    await service.execute_grant(
        principal=principal,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        clock=clock,
    )

    with pytest.raises(
        PermissionError,
        match="transaction authorization denied",
    ):
        await service.execute_grant(
            principal=principal,
            authorization_id=authorization.authorization_id,
            transaction=authorization.transaction,
            clock=clock,
        )

    assert developer_admin_service.grant_developer_admin.await_count == 1


@pytest.mark.asyncio
async def test_execute_grant_rejects_wrong_transaction(
    service: DeveloperAdminTransactionService,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
    developer_admin_service: Mock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    approve_transaction(
        transaction_authorization_service=transaction_authorization_service,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        principal=principal,
        clock=clock,
    )

    wrong_transaction = CanonicalTransaction.from_mapping(
        transaction_id=authorization.transaction.transaction_id,
        principal_id=authorization.transaction.principal_id,
        amount=authorization.transaction.amount,
        currency=authorization.transaction.currency,
        merchant_or_service=authorization.transaction.merchant_or_service,
        operation=authorization.transaction.operation,
        timestamp=authorization.transaction.timestamp,
        nonce=authorization.transaction.nonce,
        risk_context={
            "target_user_id": str(
                UUID("33333333-3333-4333-8333-333333333333")
            ),
            "operation": "grant",
            "audience": service.AUDIENCE,
        },
    )

    result = transaction_authorization_service.consume_authorization(
        principal=principal,
        authorization_id=authorization.authorization_id,
        expected_transaction=wrong_transaction,
        clock=clock,
        required_assurance_level=(
            AuthenticationAssuranceLevel.A2
        ),
    )

    assert result.decision is TransactionAuthorizationDecision.DENY
    assert (
        result.failure
        is TransactionAuthorizationFailure.INVALID_TRANSACTION_BINDING
    )
    developer_admin_service.grant_developer_admin.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_grant_uses_only_authorized_transaction_target(
    service: DeveloperAdminTransactionService,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    principal: Principal,
    target_user_id: UUID,
    different_target_user_id: UUID,
    clock: FixedClock,
    developer_admin_service: Mock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    approve_transaction(
        transaction_authorization_service=transaction_authorization_service,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        principal=principal,
        clock=clock,
        level=AuthenticationAssuranceLevel.A2,
    )

    result = await service.execute_grant(
        principal=principal,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        clock=clock,
    )

    assert result.user_id == target_user_id
    assert result.user_id != different_target_user_id

    developer_admin_service.grant_developer_admin.assert_awaited_once_with(
        actor=principal,
        user_id=target_user_id,
    )


@pytest.mark.asyncio
async def test_execute_grant_rejects_principal_substitution(
    service: DeveloperAdminTransactionService,
    transaction_authorization_service: TransactionAuthorizationApplicationService,
    principal: Principal,
    target_user_id: UUID,
    clock: FixedClock,
    developer_admin_service: Mock,
) -> None:
    authorization = service.create_grant_transaction(
        principal=principal,
        target_user_id=target_user_id,
        created_at=clock.now(),
        expires_at=clock.now() + timedelta(minutes=5),
    )

    approve_transaction(
        transaction_authorization_service=transaction_authorization_service,
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        principal=principal,
        clock=clock,
    )

    different_principal = Principal(
        user_id="user-002",
        email="user-002@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(),
    )

    with pytest.raises(
        TransactionAuthorizationApplicationError,
        match="Transaction principal does not match authenticated principal",
    ):
        await service.execute_grant(
            principal=different_principal,
            authorization_id=authorization.authorization_id,
            transaction=authorization.transaction,
            clock=clock,
        )

    developer_admin_service.grant_developer_admin.assert_not_awaited()