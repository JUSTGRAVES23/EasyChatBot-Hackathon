from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.application.authorization.authorization_service import (
    AuthenticationRequiredError,
    AuthorizationService,
)
from app.application.identity.transaction_authorization import (
    TransactionAuthorizationApplicationError,
    TransactionAuthorizationApplicationService,
)
from app.domain.authorization.permissions import Permission
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceContext,
    AuthenticationAssuranceLevel,
)
from app.domain.identity.principal import AccountStatus, Principal
from app.domain.identity.transaction_authorization import (
    CanonicalTransaction,
    TransactionAuthorizationConsumer,
    TransactionAuthorizationRegistry,
    TrustedApprovalEvidence,
)


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


def make_principal(
    user_id: str = "user-001",
) -> Principal:
    return Principal(
        user_id=user_id,
        email=f"{user_id}@example.com",
        email_verified=True,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(),
    )


def make_transaction(
    now: datetime,
) -> CanonicalTransaction:
    return CanonicalTransaction.from_mapping(
        transaction_id="tx-001",
        principal_id="user-001",
        amount="100.00",
        currency="EUR",
        merchant_or_service="merchant.example",
        operation="purchase",
        timestamp=now,
        nonce="nonce-001",
        risk_context={
            "channel": "web",
            "risk": "medium",
        },
    )


def make_assurance(
    *,
    principal_id: str = "user-001",
    level: AuthenticationAssuranceLevel = (
        AuthenticationAssuranceLevel.A2
    ),
    assurance_time: datetime,
) -> AuthenticationAssuranceContext:
    return AuthenticationAssuranceContext(
        principal_id=principal_id,
        assurance_level=level,
        authentication_time=assurance_time,
        assurance_time=assurance_time,
        authentication_method="test",
        authentication_strength="mfa",
        user_verified=True,
        phishing_resistant=(
            level is AuthenticationAssuranceLevel.A3
        ),
        issuer="test",
        subject=principal_id,
        audience="easychatbot",
        evidence_id="assurance-001",
        policy_version="test-v1",
    )


def make_service() -> TransactionAuthorizationApplicationService:
    registry = TransactionAuthorizationRegistry()

    return TransactionAuthorizationApplicationService(
        authorization_service=AuthorizationService(),
        registry=registry,
        consumer=TransactionAuthorizationConsumer(registry),
    )


def make_pending_authorization(
    *,
    service: TransactionAuthorizationApplicationService,
    principal: Principal,
    transaction: CanonicalTransaction,
    now: datetime,
) -> object:
    return service.create_pending_authorization(
        principal=principal,
        transaction=transaction,
        authorization_id="auth-001",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def test_service_requires_authenticated_principal() -> None:
    now = datetime(
        2026,
        9,
        13,
        20,
        0,
        tzinfo=timezone.utc,
    )

    service = make_service()

    inactive = Principal(
        user_id="user-001",
        email="user-001@example.com",
        email_verified=False,
        account_status=AccountStatus.ACTIVE,
        roles=frozenset(),
    )

    transaction = make_transaction(now)

    with pytest.raises(AuthenticationRequiredError):
        service.create_pending_authorization(
            principal=inactive,
            transaction=transaction,
            authorization_id="auth-001",
            created_at=now,
            expires_at=now + timedelta(minutes=5),
        )


def test_service_rejects_principal_substitution() -> None:
    now = datetime(
        2026,
        9,
        13,
        20,
        0,
        tzinfo=timezone.utc,
    )

    service = make_service()
    transaction = make_transaction(now)

    with pytest.raises(
        TransactionAuthorizationApplicationError,
        match="authenticated principal",
    ):
        service.create_pending_authorization(
            principal=make_principal("user-002"),
            transaction=transaction,
            authorization_id="auth-001",
            created_at=now,
            expires_at=now + timedelta(minutes=5),
        )


def test_service_creates_and_registers_pending_authorization() -> None:
    now = datetime(
        2026,
        9,
        13,
        20,
        0,
        tzinfo=timezone.utc,
    )

    service = make_service()
    transaction = make_transaction(now)

    pending = service.create_pending_authorization(
        principal=make_principal(),
        transaction=transaction,
        authorization_id="auth-001",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    assert (
        pending.state.value
        == "PENDING_USER_APPROVAL"
    )

    assert (
        service.registry.get("auth-001")
        == pending
    )


def test_service_consumes_w156_assurance_context_without_rederiving_assurance() -> None:
    now = datetime(
        2026,
        9,
        13,
        20,
        0,
        tzinfo=timezone.utc,
    )

    clock = FixedClock(now)
    service = make_service()
    transaction = make_transaction(now)

    pending = service.create_pending_authorization(
        principal=make_principal(),
        transaction=transaction,
        authorization_id="auth-001",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    assurance = make_assurance(
        level=AuthenticationAssuranceLevel.A2,
        assurance_time=now,
    )

    approval = object.__new__(TrustedApprovalEvidence)

    object.__setattr__(
        approval,
        "authorization_id",
        "auth-001",
    )
    object.__setattr__(
        approval,
        "transaction",
        transaction,
    )
    object.__setattr__(
        approval,
        "approved_at",
        now,
    )
    object.__setattr__(
        approval,
        "evidence_id",
        "approval-001",
    )
    object.__setattr__(
        approval,
        "assurance_context",
        assurance,
    )

    approved = service.attach_user_approval(
        principal=make_principal(),
        authorization=pending,
        approval=approval,
        clock=clock,
    )

    result = service.consume_authorization(
        principal=make_principal(),
        authorization_id=approved.authorization_id,
        expected_transaction=transaction,
        clock=clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    assert result.decision.value == "ALLOW"
    assert result.failure is None


def test_service_rejects_assurance_from_different_principal() -> None:
    now = datetime(
        2026,
        9,
        13,
        20,
        0,
        tzinfo=timezone.utc,
    )

    clock = FixedClock(now)
    service = make_service()
    transaction = make_transaction(now)

    pending = service.create_pending_authorization(
        principal=make_principal(),
        transaction=transaction,
        authorization_id="auth-001",
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    valid_assurance = make_assurance(
        principal_id="user-001",
        assurance_time=now,
    )

    approval = object.__new__(TrustedApprovalEvidence)

    object.__setattr__(
        approval,
        "authorization_id",
        "auth-001",
    )
    object.__setattr__(
        approval,
        "transaction",
        transaction,
    )
    object.__setattr__(
        approval,
        "approved_at",
        now,
    )
    object.__setattr__(
        approval,
        "evidence_id",
        "approval-001",
    )
    object.__setattr__(
        approval,
        "assurance_context",
        valid_assurance,
    )

    forged_assurance = make_assurance(
        principal_id="user-002",
        assurance_time=now,
    )

    object.__setattr__(
        approval,
        "assurance_context",
        forged_assurance,
    )

    with pytest.raises(
        TransactionAuthorizationApplicationError,
        match="authenticated principal",
    ):
        service.attach_user_approval(
            principal=make_principal(),
            authorization=pending,
            approval=approval,
            clock=clock,
        )


def test_service_rejects_invalid_required_assurance_level() -> None:
    now = datetime(
        2026,
        9,
        13,
        20,
        0,
        tzinfo=timezone.utc,
    )

    service = make_service()
    transaction = make_transaction(now)

    with pytest.raises(
        TransactionAuthorizationApplicationError,
        match="assurance level",
    ):
        service.consume_authorization(
            principal=make_principal(),
            authorization_id="missing",
            expected_transaction=transaction,
            clock=FixedClock(now),
            required_assurance_level=999,  # type: ignore[arg-type]
        )


def test_service_keeps_business_authorization_separate() -> None:
    service = make_service()

    assert isinstance(
        service.authorization_service,
        AuthorizationService,
    )

    assert not hasattr(
        service,
        "require_permission",
    )

    assert (
        Permission.FUNCTIONALITY_CONTROL
        is not None
    )


def test_service_has_no_provider_specific_dependencies() -> None:
    with open(
        "backend/app/application/identity/transaction_authorization.py",
        encoding="utf-8",
    ) as handle:
        source = handle.read()

    forbidden = (
        "zitadel",
        "keycloak",
        "webauthn",
        "passkey",
        "oidc",
        "saml",
    )

    lowered = source.lower()

    for value in forbidden:
        assert value not in lowered


def test_service_does_not_implement_mfa_or_freshness_policy() -> None:
    with open(
        "backend/app/application/identity/transaction_authorization.py",
        encoding="utf-8",
    ) as handle:
        source = handle.read().lower()

    assert "totp" not in source
    assert "otp_secret" not in source
    assert "webauthn" not in source
    assert "maximum_age" not in source
    assert (
        "authentication_time + timedelta"
        not in source
    )