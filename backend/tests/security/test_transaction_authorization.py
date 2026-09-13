from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceContext,
    AuthenticationAssuranceLevel,
)

from app.domain.identity.transaction_authorization import (
    AuthorizationIdRegistry,
    CanonicalTransaction,
    NonceRegistry,
    TransactionAuthorization,
    TransactionAuthorizationConsumer,
    TransactionAuthorizationDecision,
    TransactionAuthorizationFailure,
    TransactionAuthorizationRegistry,
    TransactionAuthorizationState,
    TrustedApprovalEvidence,
    attach_approval,
    consume,
    expire_if_due,
    transition,
)


class FixedClock:
    def __init__(self, value: datetime) -> None:
        self.value = value

    def now(self) -> datetime:
        return self.value


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 13, 20, 0, tzinfo=timezone.utc)


@pytest.fixture
def clock(now: datetime) -> FixedClock:
    return FixedClock(now)


@pytest.fixture
def transaction(now: datetime) -> CanonicalTransaction:
    return CanonicalTransaction.from_mapping(
        transaction_id="tx-001",
        principal_id="user-001",
        amount="100.00",
        currency="eur",
        merchant_or_service="merchant.example",
        operation="purchase",
        timestamp=now,
        nonce="nonce-001",
        risk_context={"risk": "medium", "channel": "web"},
    )


@pytest.fixture
def authorization(
    transaction: CanonicalTransaction,
    now: datetime,
) -> TransactionAuthorization:
    return TransactionAuthorization(
        authorization_id="auth-001",
        transaction=transaction,
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def assurance_context(
    *,
    principal_id: str = "user-001",
    level: AuthenticationAssuranceLevel = AuthenticationAssuranceLevel.A2,
    assurance_time: datetime | None = None,
) -> AuthenticationAssuranceContext:
    assurance_time = assurance_time or datetime(
        2026,
        9,
        13,
        19,
        59,
        tzinfo=timezone.utc,
    )

    return AuthenticationAssuranceContext(
        principal_id=principal_id,
        assurance_level=level,
        authentication_time=assurance_time,
        assurance_time=assurance_time,
        authentication_method="password",
        authentication_strength="mfa",
        user_verified=True,
        phishing_resistant=level is AuthenticationAssuranceLevel.A3,
        issuer="easychatbot-test",
        subject=principal_id,
        audience="easychatbot",
        evidence_id="assurance-evidence-001",
        policy_version="W15.6-policy-v1",
    )


def approved_authorization(
    authorization: TransactionAuthorization,
    clock: FixedClock,
    *,
    level: AuthenticationAssuranceLevel = AuthenticationAssuranceLevel.A2,
    principal_id: str = "user-001",
) -> TransactionAuthorization:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    approval = TrustedApprovalEvidence(
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        approved_at=clock.now(),
        evidence_id=f"approval-{authorization.authorization_id}",
        assurance_context=assurance_context(
            principal_id=principal_id,
            level=level,
            assurance_time=clock.now(),
        ),
    )

    return attach_approval(
        pending,
        approval,
        clock=clock,
    )


def test_assurance_ordering() -> None:
    assert AuthenticationAssuranceLevel.A0.value < AuthenticationAssuranceLevel.A1.value
    assert AuthenticationAssuranceLevel.A1.value < AuthenticationAssuranceLevel.A2.value
    assert AuthenticationAssuranceLevel.A2.value < AuthenticationAssuranceLevel.A3.value


def test_validated_assurance_is_immutable() -> None:
    value = assurance_context()

    with pytest.raises(FrozenInstanceError):
        value.assurance_level = AuthenticationAssuranceLevel.A3  # type: ignore[misc]


def test_assurance_requires_validated_enum_not_arbitrary_integer(
    transaction: CanonicalTransaction,
    now: datetime,
) -> None:
    context = assurance_context(
        principal_id=transaction.principal_id,
        level=AuthenticationAssuranceLevel.A2,
        assurance_time=now,
    )

    # Simulate malformed runtime data crossing the W15.6 -> W15.7
    # trust boundary. W15.6's frozen dataclass is the authoritative type;
    # this does not create a second assurance authority.
    object.__setattr__(context, "assurance_level", 999)

    with pytest.raises(TypeError, match="AuthenticationAssuranceLevel"):
        TrustedApprovalEvidence(
            authorization_id="auth-malformed-assurance",
            transaction=transaction,
            approved_at=now,
            evidence_id="malformed-assurance",
            assurance_context=context,
        )


def test_assurance_is_bound_to_transaction_principal(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    with pytest.raises(ValueError, match="principal binding"):
        TrustedApprovalEvidence(
            authorization_id=pending.authorization_id,
            transaction=pending.transaction,
            approved_at=clock.now(),
            evidence_id="approval",
            assurance_context=assurance_context(
                principal_id="different-user",
            ),
        )


def test_canonical_transaction_normalizes_monetary_amount(
    transaction: CanonicalTransaction,
) -> None:
    assert str(transaction.amount) == "100.00"


def test_canonical_transaction_does_not_use_binary_float_equality(
    transaction: CanonicalTransaction,
) -> None:
    first = CanonicalTransaction.from_mapping(
        transaction_id="tx-a",
        principal_id="user-a",
        amount=0.1,
        currency="eur",
        merchant_or_service="merchant",
        operation="purchase",
        timestamp=transaction.timestamp,
        nonce="nonce-a",
    )

    second = CanonicalTransaction.from_mapping(
        transaction_id="tx-b",
        principal_id="user-b",
        amount="0.10",
        currency="EUR",
        merchant_or_service="merchant",
        operation="purchase",
        timestamp=transaction.timestamp,
        nonce="nonce-b",
    )

    assert first.amount == second.amount
    assert str(first.amount) == "0.10"


def test_canonical_representation_is_deterministic(
    transaction: CanonicalTransaction,
) -> None:
    equivalent = CanonicalTransaction.from_mapping(
        transaction_id="tx-001",
        principal_id="user-001",
        amount="100.00",
        currency="EUR",
        merchant_or_service="merchant.example",
        operation="purchase",
        timestamp=transaction.timestamp,
        nonce="nonce-001",
        risk_context={"channel": "web", "risk": "medium"},
    )

    assert (
        transaction.canonical_representation()
        == equivalent.canonical_representation()
    )


def test_every_security_field_changes_canonical_binding(
    transaction: CanonicalTransaction,
) -> None:
    values = {
        "transaction_id": "tx-changed",
        "principal_id": "user-changed",
        "operation": "refund",
        "amount": "101.00",
        "currency": "USD",
        "merchant_or_service": "other.example",
        "timestamp": transaction.timestamp + timedelta(seconds=1),
        "nonce": "nonce-changed",
        "risk_context": {"risk": "high", "channel": "web"},
    }

    for field, value in values.items():
        kwargs = {
            "transaction_id": transaction.transaction_id,
            "principal_id": transaction.principal_id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "merchant_or_service": transaction.merchant_or_service,
            "operation": transaction.operation,
            "timestamp": transaction.timestamp,
            "nonce": transaction.nonce,
            "risk_context": dict(transaction.risk_context),
        }

        kwargs[field] = value

        changed = CanonicalTransaction.from_mapping(**kwargs)

        assert (
            changed.canonical_representation()
            != transaction.canonical_representation()
        ), field


def test_transaction_binding_covers_required_security_fields(
    transaction: CanonicalTransaction,
) -> None:
    representation = transaction.canonical_representation()

    for value in (
        transaction.transaction_id,
        transaction.principal_id,
        transaction.operation,
        transaction.nonce,
        transaction.currency,
        transaction.merchant_or_service,
        "medium",
        "web",
        "100.00",
    ):
        assert value in representation


def test_trusted_approval_evidence_is_immutable(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    approved = approved_authorization(authorization, clock)

    assert approved.approval is not None

    with pytest.raises(FrozenInstanceError):
        approved.approval.evidence_id = "forged"  # type: ignore[misc]


def test_caller_boolean_cannot_create_trusted_approval() -> None:
    assert "approved" not in TrustedApprovalEvidence.__annotations__


def test_a3_assurance_is_not_transaction_approval(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    a3 = assurance_context(
        level=AuthenticationAssuranceLevel.A3,
    )

    approval = TrustedApprovalEvidence(
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        approved_at=clock.now(),
        evidence_id="a3",
        assurance_context=a3,
    )

    assert pending.state is TransactionAuthorizationState.PENDING_USER_APPROVAL
    assert approval.assurance_level is AuthenticationAssuranceLevel.A3


def test_future_dated_approval_fails_closed(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    approval = TrustedApprovalEvidence(
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        approved_at=clock.now() + timedelta(minutes=1),
        evidence_id="future",
        assurance_context=assurance_context(
            assurance_time=clock.now(),
        ),
    )

    with pytest.raises(ValueError, match="future-dated"):
        attach_approval(
            pending,
            approval,
            clock=clock,
        )


def test_trusted_clock_is_used_for_expiry(
    authorization: TransactionAuthorization,
    now: datetime,
) -> None:
    future_clock = FixedClock(now + timedelta(minutes=10))

    approved = approved_authorization(
        authorization,
        FixedClock(now),
    )

    result = consume(
        approved,
        clock=future_clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    assert result.decision is TransactionAuthorizationDecision.DENY
    assert result.failure is TransactionAuthorizationFailure.EXPIRED


def test_future_dated_assurance_does_not_bypass_trusted_time(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    future_context = assurance_context(
        level=AuthenticationAssuranceLevel.A3,
        assurance_time=clock.now() + timedelta(hours=1),
    )

    approval = TrustedApprovalEvidence(
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        approved_at=clock.now(),
        evidence_id="future-assurance",
        assurance_context=future_context,
    )

    with pytest.raises(ValueError, match="future"):
        attach_approval(
            pending,
            approval,
            clock=clock,
        )


def test_legal_lifecycle_transitions(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    approved = approved_authorization(
        authorization,
        clock,
    )

    consumed = transition(
        approved,
        TransactionAuthorizationState.CONSUMED,
    )

    assert pending.state is TransactionAuthorizationState.PENDING_USER_APPROVAL
    assert approved.state is TransactionAuthorizationState.APPROVED
    assert consumed.state is TransactionAuthorizationState.CONSUMED


def test_illegal_lifecycle_transitions_fail_closed(
    authorization: TransactionAuthorization,
) -> None:
    with pytest.raises(ValueError):
        transition(
            authorization,
            TransactionAuthorizationState.CONSUMED,
        )

    pending = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    with pytest.raises(ValueError):
        transition(
            pending,
            TransactionAuthorizationState.CONSUMED,
        )


def test_unapproved_transaction_denies(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    result = consume(
        authorization,
        clock=clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    assert result.decision is TransactionAuthorizationDecision.DENY
    assert result.failure is TransactionAuthorizationFailure.INVALID_APPROVAL


def test_nonce_registry_rejects_replay() -> None:
    registry = NonceRegistry()

    registry.register("nonce-1")

    with pytest.raises(ValueError, match="NONCE_REPLAY"):
        registry.register("nonce-1")


def test_authorization_id_registry_rejects_duplicates() -> None:
    registry = AuthorizationIdRegistry()

    registry.register("auth-1")

    with pytest.raises(ValueError, match="DUPLICATE_AUTHORIZATION_ID"):
        registry.register("auth-1")


def test_transaction_registry_rejects_duplicate_authorization_id(
    authorization: TransactionAuthorization,
) -> None:
    registry = TransactionAuthorizationRegistry()

    registry.register(authorization)

    with pytest.raises(ValueError, match="DUPLICATE_AUTHORIZATION_ID"):
        registry.register(authorization)


def test_transaction_registry_rejects_duplicate_nonce(
    authorization: TransactionAuthorization,
    transaction: CanonicalTransaction,
    now: datetime,
) -> None:
    registry = TransactionAuthorizationRegistry()

    registry.register(authorization)

    duplicate_transaction = CanonicalTransaction.from_mapping(
        transaction_id="tx-duplicate",
        principal_id=transaction.principal_id,
        amount=transaction.amount,
        currency=transaction.currency,
        merchant_or_service=transaction.merchant_or_service,
        operation=transaction.operation,
        timestamp=transaction.timestamp,
        nonce=transaction.nonce,
    )

    duplicate = TransactionAuthorization(
        authorization_id="auth-duplicate",
        transaction=duplicate_transaction,
        created_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    with pytest.raises(ValueError, match="NONCE_REPLAY"):
        registry.register(duplicate)


def test_registry_replace_requires_expected_current_state(
    authorization: TransactionAuthorization,
) -> None:
    registry = TransactionAuthorizationRegistry()

    registry.register(authorization)

    replacement = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    wrong_expected = transition(
        authorization,
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    )

    assert not registry.replace(
        authorization.authorization_id,
        wrong_expected,
        replacement,
    )

    assert registry.replace(
        authorization.authorization_id,
        authorization,
        replacement,
    )


def test_atomic_consume_is_single_use(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    approved = approved_authorization(
        authorization,
        clock,
    )

    registry = TransactionAuthorizationRegistry()
    registry.register(approved)

    consumer = TransactionAuthorizationConsumer(registry)

    first = consumer.consume_once(
        authorization.authorization_id,
        expected_transaction=authorization.transaction,
        clock=clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    second = consumer.consume_once(
        authorization.authorization_id,
        expected_transaction=authorization.transaction,
        clock=clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    assert first.decision is TransactionAuthorizationDecision.ALLOW
    assert second.decision is TransactionAuthorizationDecision.DENY
    assert second.failure is TransactionAuthorizationFailure.ALREADY_CONSUMED


def test_concurrent_consumption_has_exactly_one_success(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    approved = approved_authorization(
        authorization,
        clock,
    )

    registry = TransactionAuthorizationRegistry()
    registry.register(approved)

    consumer = TransactionAuthorizationConsumer(registry)

    def attempt():
        return consumer.consume_once(
            authorization.authorization_id,
            expected_transaction=authorization.transaction,
            clock=clock,
            required_assurance_level=AuthenticationAssuranceLevel.A2,
        )

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(
            executor.map(
                lambda _: attempt(),
                range(16),
            )
        )

    allows = [
        result
        for result in results
        if result.decision is TransactionAuthorizationDecision.ALLOW
    ]

    assert len(allows) == 1


def test_transaction_mismatch_denies(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    approved = approved_authorization(
        authorization,
        clock,
    )

    registry = TransactionAuthorizationRegistry()
    registry.register(approved)

    consumer = TransactionAuthorizationConsumer(registry)

    wrong_transaction = CanonicalTransaction.from_mapping(
        transaction_id="different",
        principal_id=authorization.transaction.principal_id,
        amount=authorization.transaction.amount,
        currency=authorization.transaction.currency,
        merchant_or_service=authorization.transaction.merchant_or_service,
        operation=authorization.transaction.operation,
        timestamp=authorization.transaction.timestamp,
        nonce="different-nonce",
    )

    result = consumer.consume_once(
        authorization.authorization_id,
        expected_transaction=wrong_transaction,
        clock=clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    assert result.decision is TransactionAuthorizationDecision.DENY
    assert result.failure is TransactionAuthorizationFailure.INVALID_TRANSACTION_BINDING


def test_insufficient_assurance_denies(
    authorization: TransactionAuthorization,
    clock: FixedClock,
) -> None:
    approved = approved_authorization(
        authorization,
        clock,
        level=AuthenticationAssuranceLevel.A1,
    )

    registry = TransactionAuthorizationRegistry()
    registry.register(approved)

    consumer = TransactionAuthorizationConsumer(registry)

    result = consumer.consume_once(
        authorization.authorization_id,
        expected_transaction=authorization.transaction,
        clock=clock,
        required_assurance_level=AuthenticationAssuranceLevel.A2,
    )

    assert result.decision is TransactionAuthorizationDecision.DENY
    assert (
        result.failure
        is TransactionAuthorizationFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE
    )


def test_transaction_authorization_does_not_implement_business_authorization(
    authorization: TransactionAuthorization,
) -> None:
    assert not hasattr(authorization, "roles")
    assert not hasattr(authorization, "permissions")


def test_no_raw_secret_fields_are_present_in_canonical_representation(
    transaction: CanonicalTransaction,
) -> None:
    representation = transaction.canonical_representation().lower()

    for secret_name in (
        "password",
        "access_token",
        "refresh_token",
        "otp_secret",
        "private_key",
    ):
        assert secret_name not in representation