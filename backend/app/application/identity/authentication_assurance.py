from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from app.domain.identity.authentication_assurance import (
    AuthenticationAssuranceContext,
    AuthenticationAssuranceDecision,
    AuthenticationAssuranceDecisionResult,
    AuthenticationAssuranceFailure,
    AuthenticationAssuranceLevel,
    TrustedClock,
    ValidatedAuthenticationEvidence,
)


class AuthenticationAssurancePolicy(Protocol):
    """
    Centrally supplied authentication-assurance policy.

    Business services must not implement their own freshness or
    assurance rules.
    """

    def maximum_age(
        self,
        level: AuthenticationAssuranceLevel,
    ) -> timedelta:
        ...

    def derive_level(
        self,
        evidence: ValidatedAuthenticationEvidence,
    ) -> AuthenticationAssuranceLevel:
        ...


@dataclass(frozen=True, slots=True)
class StaticAuthenticationAssurancePolicy:
    """
    Explicit policy implementation useful for application wiring and tests.

    The policy remains centrally supplied to the assurance service.
    Business services do not receive or implement these rules.

    The default values are deliberately conservative implementation
    defaults only; production values should be supplied by application
    configuration/GRC policy.
    """

    a0_max_age: timedelta = timedelta(hours=12)
    a1_max_age: timedelta = timedelta(minutes=15)
    a2_max_age: timedelta = timedelta(minutes=5)
    a3_max_age: timedelta = timedelta(minutes=2)

    def maximum_age(
        self,
        level: AuthenticationAssuranceLevel,
    ) -> timedelta:
        if level == AuthenticationAssuranceLevel.A0:
            return self.a0_max_age

        if level == AuthenticationAssuranceLevel.A1:
            return self.a1_max_age

        if level == AuthenticationAssuranceLevel.A2:
            return self.a2_max_age

        if level == AuthenticationAssuranceLevel.A3:
            return self.a3_max_age

        raise ValueError(f"Unsupported assurance level: {level!r}")

    def derive_level(
        self,
        evidence: ValidatedAuthenticationEvidence,
    ) -> AuthenticationAssuranceLevel:
        """
        Derive assurance from validated authentication evidence.

        A caller cannot simply provide `assurance_level=A3` because
        ValidatedAuthenticationEvidence contains no assurance-level field.

        A3 requires phishing-resistant authentication plus user
        verification.

        A2 requires MFA-strength evidence.

        A1 requires stronger-than-normal authentication evidence.

        A0 represents normal authenticated evidence.
        """

        method = evidence.authentication_method.strip().lower()
        strength = evidence.authentication_strength.strip().lower()

        if not method or not strength:
            raise ValueError("Authentication method and strength are required")

        if evidence.phishing_resistant and evidence.user_verified:
            return AuthenticationAssuranceLevel.A3

        if (
            evidence.user_verified
            and strength in {
                "mfa",
                "multi_factor",
                "multifactor",
                "strong",
            }
        ):
            return AuthenticationAssuranceLevel.A2

        if strength in {
            "reauthenticated",
            "recent_reauthentication",
            "mfa",
            "multi_factor",
            "multifactor",
            "strong",
        }:
            return AuthenticationAssuranceLevel.A1

        return AuthenticationAssuranceLevel.A0


class AuthenticationAssuranceService:
    """
    Central authentication-assurance evaluator.

    Responsibilities:
      - validate evidence
      - bind evidence to principal
      - bind evidence to audience
      - derive assurance from validated evidence
      - evaluate freshness using trusted server/application time
      - return deterministic ALLOW/DENY

    Explicit non-responsibilities:
      - business authorization
      - transaction authorization
      - MFA implementation
      - external IAM protocol handling
      - password authentication
    """

    def __init__(
        self,
        *,
        policy: AuthenticationAssurancePolicy,
        clock: TrustedClock,
    ) -> None:
        self._policy = policy
        self._clock = clock

    def require(
        self,
        *,
        principal_id: str,
        required_level: AuthenticationAssuranceLevel,
        expected_audience: str,
        evidence: ValidatedAuthenticationEvidence | None,
    ) -> AuthenticationAssuranceDecisionResult:
        """
        Require a minimum authentication-assurance level.

        The caller supplies the required level, not the achieved level.

        The achieved level is derived from validated evidence.

        All validation failures fail closed.
        """

        if not principal_id.strip():
            return self._deny(
                AuthenticationAssuranceFailure.UNAUTHENTICATED
            )

        if evidence is None:
            return self._deny(
                AuthenticationAssuranceFailure.UNAUTHENTICATED
            )

        if not expected_audience.strip():
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUDIENCE
            )

        evidence_failure = self._validate_evidence(
            principal_id=principal_id,
            expected_audience=expected_audience,
            evidence=evidence,
        )

        if evidence_failure is not None:
            return self._deny(evidence_failure)

        try:
            actual_level = self._policy.derive_level(evidence)
        except (TypeError, ValueError, AttributeError):
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
            )

        now = self._trusted_now()

        if now is None:
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
            )

        authentication_time = evidence.authentication_time

        if authentication_time.tzinfo is None:
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
            )

        authentication_time = authentication_time.astimezone(timezone.utc)
        now = now.astimezone(timezone.utc)

        # Future authentication timestamps are invalid. This also prevents
        # caller-controlled timestamps from being used to manufacture
        # apparently fresh authentication evidence.
        if authentication_time > now:
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
            )

        try:
            maximum_age = self._policy.maximum_age(actual_level)
        except (TypeError, ValueError, AttributeError):
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
            )

        if maximum_age < timedelta(0):
            return self._deny(
                AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE
            )

        age = now - authentication_time

        if age > maximum_age:
            return self._deny(
                AuthenticationAssuranceFailure.STALE_AUTHENTICATION_ASSURANCE
            )

        if actual_level < required_level:
            return self._deny(
                AuthenticationAssuranceFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE
            )

        context = AuthenticationAssuranceContext(
            principal_id=evidence.principal_id,
            assurance_level=actual_level,
            authentication_time=authentication_time,
            assurance_time=now,
            authentication_method=evidence.authentication_method,
            authentication_strength=evidence.authentication_strength,
            user_verified=evidence.user_verified,
            phishing_resistant=evidence.phishing_resistant,
            issuer=evidence.issuer,
            subject=evidence.subject,
            audience=evidence.audience,
            evidence_id=evidence.evidence_id,
            policy_version=evidence.policy_version,
        )

        return AuthenticationAssuranceDecisionResult(
            decision=AuthenticationAssuranceDecision.ALLOW,
            context=context,
            failure=None,
        )

    @staticmethod
    def _validate_evidence(
        *,
        principal_id: str,
        expected_audience: str,
        evidence: ValidatedAuthenticationEvidence,
    ) -> AuthenticationAssuranceFailure | None:
        required_strings = (
            evidence.principal_id,
            evidence.issuer,
            evidence.subject,
            evidence.audience,
            evidence.authentication_method,
            evidence.authentication_strength,
            evidence.evidence_id,
            evidence.policy_version,
        )

        if any(
            not isinstance(value, str) or not value.strip()
            for value in required_strings
        ):
            return AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE

        if evidence.principal_id != principal_id:
            return AuthenticationAssuranceFailure.INVALID_PRINCIPAL_BINDING

        if evidence.audience != expected_audience:
            return AuthenticationAssuranceFailure.INVALID_AUDIENCE

        if not isinstance(evidence.authentication_time, datetime):
            return AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE

        if not isinstance(evidence.user_verified, bool):
            return AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE

        if not isinstance(evidence.phishing_resistant, bool):
            return AuthenticationAssuranceFailure.INVALID_AUTHENTICATION_EVIDENCE

        return None

    def _trusted_now(self) -> datetime | None:
        try:
            now = self._clock.now()
        except Exception:
            return None

        if not isinstance(now, datetime):
            return None

        if now.tzinfo is None:
            return None

        return now

    @staticmethod
    def _deny(
        failure: AuthenticationAssuranceFailure,
    ) -> AuthenticationAssuranceDecisionResult:
        return AuthenticationAssuranceDecisionResult(
            decision=AuthenticationAssuranceDecision.DENY,
            context=None,
            failure=failure,
        )
