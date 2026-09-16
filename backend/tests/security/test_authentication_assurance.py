from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from app.application.identity.authentication_assurance import (
    AuthenticationAssuranceService,
    StaticAuthenticationAssurancePolicy,
)
from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceDecision,
    AuthenticationAssuranceFailure,
    AuthenticationAssuranceLevel,
    ValidatedAuthenticationEvidence,
)


class FixedClock:
    def __init__(self, current_time: datetime) -> None:
        self.current_time = current_time
        self.calls = 0

    def now(self) -> datetime:
        self.calls += 1
        return self.current_time


def make_evidence(
    *,
    principal_id: str = "user-123",
    audience: str = "easychatbot",
    authentication_time: datetime | None = None,
    authentication_method: str = "password",
    authentication_strength: str = "normal",
    user_verified: bool = False,
    phishing_resistant: bool = False,
) -> ValidatedAuthenticationEvidence:
    if authentication_time is None:
        authentication_time = datetime(
            2026,
            9,
            13,
            12,
            0,
            tzinfo=timezone.utc,
        )

    return ValidatedAuthenticationEvidence(
        principal_id=principal_id,
        issuer="trusted-test-issuer",
        subject="subject-123",
        audience=audience,
        authentication_time=authentication_time,
        authentication_method=authentication_method,
        authentication_strength=authentication_strength,
        user_verified=user_verified,
        phishing_resistant=phishing_resistant,
        evidence_id="evidence-123",
        policy_version="test-policy-v1",
    )


def make_service(
    *,
    now: datetime | None = None,
    policy: StaticAuthenticationAssurancePolicy | None = None,
) -> tuple[AuthenticationAssuranceService, FixedClock]:
    if now is None:
        now = datetime(
            2026,
            9,
            13,
            12,
            1,
            tzinfo=timezone.utc,
        )

    clock = FixedClock(now)

    if policy is None:
        policy = StaticAuthenticationAssurancePolicy()

    service = AuthenticationAssuranceService(
        policy=policy,
        clock=clock,
    )

    return service, clock


def test_assurance_ordering_is_monotonic() -> None:
    assert (
        AuthenticationAssuranceLevel.A0
        < AuthenticationAssuranceLevel.A1
        < AuthenticationAssuranceLevel.A2
        < AuthenticationAssuranceLevel.A3
    )


def test_a3_cannot_be_caller_forged_by_setting_an_assurance_level() -> None:
    evidence = make_evidence()

    assert not hasattr(evidence, "assurance_level")

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A3,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE
    )


def test_a3_requires_phishing_resistant_user_verified_evidence() -> None:
    evidence = make_evidence(
        authentication_method="passkey",
        authentication_strength="strong",
        user_verified=True,
        phishing_resistant=True,
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A3,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.ALLOW
    assert result.failure is None
    assert result.context is not None
    assert result.context.assurance_level is AuthenticationAssuranceLevel.A3


def test_trusted_clock_is_used_for_freshness() -> None:
    trusted_now = datetime(
        2026,
        9,
        13,
        12,
        10,
        tzinfo=timezone.utc,
    )

    evidence = make_evidence(
        authentication_time=datetime(
            2026,
            9,
            13,
            12,
            9,
            tzinfo=timezone.utc,
        )
    )

    service, clock = make_service(now=trusted_now)

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert clock.calls == 1
    assert result.decision is AuthenticationAssuranceDecision.ALLOW
    assert result.context is not None
    assert result.context.assurance_time == trusted_now


def test_caller_controlled_future_timestamp_cannot_create_fresh_assurance() -> None:
    trusted_now = datetime(
        2026,
        9,
        13,
        12,
        0,
        tzinfo=timezone.utc,
    )

    future_authentication_time = trusted_now + timedelta(hours=1)

    evidence = make_evidence(
        authentication_time=future_authentication_time,
    )

    service, _ = make_service(now=trusted_now)

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
    )


def test_principal_binding_is_enforced() -> None:
    evidence = make_evidence(principal_id="different-user")

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.INVALID_PRINCIPAL_BINDING
    )


def test_audience_binding_is_enforced() -> None:
    evidence = make_evidence(audience="another-application")

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert result.failure is AuthenticationAssuranceFailure.INVALID_AUDIENCE


def test_missing_expected_audience_fails_closed() -> None:
    evidence = make_evidence()

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert result.failure is AuthenticationAssuranceFailure.INVALID_AUDIENCE


def test_immutable_evidence_cannot_be_mutated() -> None:
    evidence = make_evidence()

    with pytest.raises(FrozenInstanceError):
        evidence.principal_id = "attacker"


def test_successful_evaluation_returns_allow() -> None:
    evidence = make_evidence(
        authentication_strength="normal",
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.ALLOW
    assert result.failure is None
    assert result.context is not None
    assert result.context.principal_id == "user-123"
    assert result.context.audience == "easychatbot"


def test_insufficient_assurance_fails_closed() -> None:
    evidence = make_evidence(
        authentication_strength="normal",
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A2,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE
    )


def test_stale_assurance_fails_closed() -> None:
    now = datetime(
        2026,
        9,
        13,
        12,
        10,
        tzinfo=timezone.utc,
    )

    evidence = make_evidence(
        authentication_time=datetime(
            2026,
            9,
            13,
            11,
            0,
            tzinfo=timezone.utc,
        )
    )

    policy = StaticAuthenticationAssurancePolicy(
        a0_max_age=timedelta(minutes=5),
    )

    service, _ = make_service(
        now=now,
        policy=policy,
    )

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.STALE_AUTHENTICATION_ASSURANCE
    )


def test_unauthenticated_evidence_fails_closed() -> None:
    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=None,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert result.failure is AuthenticationAssuranceFailure.UNAUTHENTICATED


def test_naive_authentication_timestamp_fails_closed() -> None:
    evidence = make_evidence(
        authentication_time=datetime(
            2026,
            9,
            13,
            12,
            0,
        )
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
    )


def test_higher_assurance_does_not_grant_authorization() -> None:
    """
    This service returns authentication assurance only.

    There is intentionally no authorization permission/role decision
    in the result.
    """

    evidence = make_evidence(
        authentication_method="passkey",
        authentication_strength="strong",
        user_verified=True,
        phishing_resistant=True,
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A3,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.ALLOW
    assert result.context is not None

    assert not hasattr(result.context, "permission")
    assert not hasattr(result.context, "authorized")
    assert not hasattr(result.context, "transaction_authorized")


def test_transaction_authorization_remains_separate() -> None:
    evidence = make_evidence(
        authentication_method="passkey",
        authentication_strength="strong",
        user_verified=True,
        phishing_resistant=True,
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A3,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.ALLOW
    assert result.context is not None

    assert not hasattr(result.context, "transaction_id")
    assert not hasattr(result.context, "amount")
    assert not hasattr(result.context, "currency")
    assert not hasattr(result.context, "merchant")
    assert not hasattr(result.context, "nonce")


def test_invalid_evidence_fields_fail_closed() -> None:
    evidence = make_evidence(
        authentication_method="",
    )

    service, _ = make_service()

    result = service.require(
        principal_id="user-123",
        required_level=AuthenticationAssuranceLevel.A0,
        expected_audience="easychatbot",
        evidence=evidence,
    )

    assert result.decision is AuthenticationAssuranceDecision.DENY
    assert (
        result.failure
        is AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
    )
