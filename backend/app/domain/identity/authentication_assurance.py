from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum
from typing import Protocol


class AuthenticationAssuranceLevel(IntEnum):
    """
    Monotonic authentication-assurance levels.

    A higher level represents stronger authentication assurance.
    Higher assurance does NOT imply authorization.
    """

    A0 = 0
    A1 = 1
    A2 = 2
    A3 = 3


class AuthenticationAssuranceDecision(str, Enum):
    """Deterministic result of an assurance evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"


class AuthenticationAssuranceFailure(str, Enum):
    """Deterministic fail-closed assurance failures."""

    UNAUTHENTICATED = "UNAUTHENTICATED"
    INVALID_AUTHENTICATION_EVIDENCE = "INVALID_AUTHENTICATION_EVIDENCE"
    INVALID_PRINCIPAL_BINDING = "INVALID_PRINCIPAL_BINDING"
    INVALID_AUDIENCE = "INVALID_AUDIENCE"
    STALE_AUTHENTICATION_ASSURANCE = "STALE_AUTHENTICATION_ASSURANCE"
    INSUFFICIENT_AUTHENTICATION_ASSURANCE = (
        "INSUFFICIENT_AUTHENTICATION_ASSURANCE"
    )


class TrustedClock(Protocol):
    """
    Trusted application/server clock.

    Freshness decisions MUST use this clock rather than timestamps
    supplied by the caller.
    """

    def now(self) -> datetime:
        ...


@dataclass(frozen=True, slots=True)
class ValidatedAuthenticationEvidence:
    """
    Immutable authentication evidence produced after Identity Adapter
    validation.

    This object deliberately contains NO caller-supplied assurance level.
    Assurance is derived by the central AuthenticationAssuranceService
    from validated evidence and centrally supplied policy.

    Raw credentials, access tokens, refresh tokens, OTP secrets, and
    WebAuthn private material MUST NOT be stored here.
    """

    principal_id: str
    issuer: str
    subject: str
    audience: str
    authentication_time: datetime
    authentication_method: str
    authentication_strength: str
    user_verified: bool
    phishing_resistant: bool
    evidence_id: str
    policy_version: str


@dataclass(frozen=True, slots=True)
class AuthenticationAssuranceContext:
    """
    Immutable, validated assurance context returned after successful
    assurance evaluation.

    The context describes authentication assurance only. It does not
    grant business authorization and does not represent transaction
    authorization.
    """

    principal_id: str
    assurance_level: AuthenticationAssuranceLevel
    authentication_time: datetime
    assurance_time: datetime
    authentication_method: str
    authentication_strength: str
    user_verified: bool
    phishing_resistant: bool
    issuer: str
    subject: str
    audience: str
    evidence_id: str
    policy_version: str


@dataclass(frozen=True, slots=True)
class AuthenticationAssuranceDecisionResult:
    """
    Deterministic assurance decision.

    ALLOW contains a validated context.
    DENY contains a deterministic failure reason.
    """

    decision: AuthenticationAssuranceDecision
    context: AuthenticationAssuranceContext | None = None
    failure: AuthenticationAssuranceFailure | None = None
