from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from threading import Lock
from typing import Mapping, Protocol


class TransactionAuthorizationState(str, Enum):
    CREATED = "CREATED"
    PENDING_USER_APPROVAL = "PENDING_USER_APPROVAL"
    APPROVED = "APPROVED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class TransactionAuthorizationFailure(str, Enum):
    INVALID_TRANSACTION = "INVALID_TRANSACTION"
    INVALID_PRINCIPAL_BINDING = "INVALID_PRINCIPAL_BINDING"
    INVALID_TRANSACTION_BINDING = "INVALID_TRANSACTION_BINDING"
    INVALID_OPERATION_BINDING = "INVALID_OPERATION_BINDING"
    INVALID_AMOUNT_BINDING = "INVALID_AMOUNT_BINDING"
    INVALID_CURRENCY_BINDING = "INVALID_CURRENCY_BINDING"
    INVALID_MERCHANT_BINDING = "INVALID_MERCHANT_BINDING"
    INVALID_RISK_CONTEXT = "INVALID_RISK_CONTEXT"
    INVALID_NONCE = "INVALID_NONCE"
    NONCE_REPLAY = "NONCE_REPLAY"
    INVALID_APPROVAL = "INVALID_APPROVAL"
    INSUFFICIENT_AUTHENTICATION_ASSURANCE = (
        "INSUFFICIENT_AUTHENTICATION_ASSURANCE"
    )
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    ALREADY_CONSUMED = "ALREADY_CONSUMED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    DUPLICATE_AUTHORIZATION_ID = "DUPLICATE_AUTHORIZATION_ID"
    INVALID_ASSURANCE_PROVENANCE = "INVALID_ASSURANCE_PROVENANCE"


class TransactionAuthorizationDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class AuthenticationAssuranceLevel(int, Enum):
    A0 = 0
    A1 = 1
    A2 = 2
    A3 = 3


class TrustedClock(Protocol):
    def now(self) -> datetime:
        ...


@dataclass(frozen=True, slots=True)
class ValidatedAuthenticationAssurance:
    """
    W15.6 trust-boundary output consumed by W15.7.

    This object is intentionally immutable. W15.7 does not create,
    strengthen, or derive an assurance level.
    """

    principal_id: str
    assurance_level: AuthenticationAssuranceLevel
    evidence_id: str
    assurance_time: datetime
    policy_version: str

    def __post_init__(self) -> None:
        if not self.principal_id:
            raise ValueError("principal_id must not be empty")
        if not self.evidence_id:
            raise ValueError("evidence_id must not be empty")
        if not self.policy_version:
            raise ValueError("policy_version must not be empty")

        object.__setattr__(
            self,
            "assurance_time",
            _normalize_datetime(self.assurance_time),
        )


@dataclass(frozen=True, slots=True)
class TransactionAuthorizationDecisionResult:
    decision: TransactionAuthorizationDecision
    failure: TransactionAuthorizationFailure | None = None


@dataclass(frozen=True, slots=True)
class CanonicalTransaction:
    transaction_id: str
    principal_id: str
    amount: Decimal | None
    currency: str | None
    merchant_or_service: str | None
    operation: str
    timestamp: datetime
    nonce: str
    risk_context: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.transaction_id:
            raise ValueError("transaction_id must not be empty")
        if not self.principal_id:
            raise ValueError("principal_id must not be empty")
        if not self.operation:
            raise ValueError("operation must not be empty")
        if not self.nonce:
            raise ValueError("nonce must not be empty")

        if self.amount is not None:
            normalized = Decimal(str(self.amount))
            if not normalized.is_finite():
                raise ValueError("amount must be finite")
            object.__setattr__(
                self,
                "amount",
                normalized.quantize(Decimal("0.01")),
            )

        if self.currency is not None:
            normalized_currency = self.currency.strip().upper()
            if not normalized_currency:
                raise ValueError("currency must not be empty")
            object.__setattr__(self, "currency", normalized_currency)

        if self.merchant_or_service is not None:
            normalized_merchant = self.merchant_or_service.strip()
            if not normalized_merchant:
                raise ValueError("merchant_or_service must not be empty")
            object.__setattr__(
                self,
                "merchant_or_service",
                normalized_merchant,
            )

        object.__setattr__(self, "operation", self.operation.strip())
        object.__setattr__(
            self,
            "timestamp",
            _normalize_datetime(self.timestamp),
        )
        object.__setattr__(
            self,
            "risk_context",
            tuple(
                sorted(
                    (str(k), str(v))
                    for k, v in self.risk_context
                )
            ),
        )

    @classmethod
    def from_mapping(
        cls,
        *,
        transaction_id: str,
        principal_id: str,
        amount: Decimal | str | int | float | None,
        currency: str | None,
        merchant_or_service: str | None,
        operation: str,
        timestamp: datetime,
        nonce: str,
        risk_context: Mapping[str, str] | None = None,
    ) -> "CanonicalTransaction":
        return cls(
            transaction_id=transaction_id,
            principal_id=principal_id,
            amount=None if amount is None else Decimal(str(amount)),
            currency=currency,
            merchant_or_service=merchant_or_service,
            operation=operation,
            timestamp=timestamp,
            nonce=nonce,
            risk_context=tuple(
                sorted(
                    (str(k), str(v))
                    for k, v in (risk_context or {}).items()
                )
            ),
        )

    def canonical_representation(self) -> str:
        payload = {
            "amount": (
                None
                if self.amount is None
                else format(self.amount, "f")
            ),
            "currency": self.currency,
            "merchant_or_service": self.merchant_or_service,
            "nonce": self.nonce,
            "operation": self.operation,
            "principal_id": self.principal_id,
            "risk_context": [
                [key, value]
                for key, value in self.risk_context
            ],
            "timestamp": self.timestamp.isoformat(),
            "transaction_id": self.transaction_id,
        }

        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )


@dataclass(frozen=True, slots=True)
class TrustedApprovalEvidence:
    """
    Approval evidence must already have crossed a trusted application
    boundary. W15.7 never derives authentication assurance itself.
    """

    authorization_id: str
    transaction: CanonicalTransaction
    approved_at: datetime
    evidence_id: str
    assurance: ValidatedAuthenticationAssurance

    def __post_init__(self) -> None:
        if not self.authorization_id:
            raise ValueError("authorization_id must not be empty")
        if not self.evidence_id:
            raise ValueError("evidence_id must not be empty")

        object.__setattr__(
            self,
            "approved_at",
            _normalize_datetime(self.approved_at),
        )

    @property
    def assurance_level(self) -> AuthenticationAssuranceLevel:
        return self.assurance.assurance_level


@dataclass(frozen=True, slots=True)
class TransactionAuthorization:
    authorization_id: str
    transaction: CanonicalTransaction
    created_at: datetime
    expires_at: datetime
    state: TransactionAuthorizationState = TransactionAuthorizationState.CREATED
    approval: TrustedApprovalEvidence | None = None

    def __post_init__(self) -> None:
        if not self.authorization_id:
            raise ValueError("authorization_id must not be empty")

        created = _normalize_datetime(self.created_at)
        expires = _normalize_datetime(self.expires_at)

        if expires <= created:
            raise ValueError("expires_at must be after created_at")

        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "expires_at", expires)

        if self.approval is not None:
            if self.approval.authorization_id != self.authorization_id:
                raise ValueError("approval authorization binding mismatch")

            if self.approval.assurance.principal_id != self.transaction.principal_id:
                raise ValueError("approval assurance principal binding mismatch")

            if (
                self.approval.transaction.canonical_representation()
                != self.transaction.canonical_representation()
            ):
                raise ValueError("approval transaction binding mismatch")


_ALLOWED_TRANSITIONS = {
    TransactionAuthorizationState.CREATED: {
        TransactionAuthorizationState.PENDING_USER_APPROVAL,
    },
    TransactionAuthorizationState.PENDING_USER_APPROVAL: {
        TransactionAuthorizationState.APPROVED,
        TransactionAuthorizationState.REJECTED,
    },
    TransactionAuthorizationState.APPROVED: {
        TransactionAuthorizationState.CONSUMED,
        TransactionAuthorizationState.REVOKED,
        TransactionAuthorizationState.EXPIRED,
    },
    TransactionAuthorizationState.CONSUMED: set(),
    TransactionAuthorizationState.EXPIRED: set(),
    TransactionAuthorizationState.REJECTED: set(),
    TransactionAuthorizationState.REVOKED: set(),
}


class NonceRegistry:
    """Trusted process-local uniqueness boundary for authorization nonces."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._nonces: set[str] = set()

    def register(self, nonce: str) -> None:
        if not nonce:
            raise ValueError("nonce must not be empty")

        with self._lock:
            if nonce in self._nonces:
                raise ValueError(
                    TransactionAuthorizationFailure.NONCE_REPLAY.value
                )
            self._nonces.add(nonce)


class AuthorizationIdRegistry:
    """Trusted process-local uniqueness boundary for authorization IDs."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._authorization_ids: set[str] = set()

    def register(self, authorization_id: str) -> None:
        if not authorization_id:
            raise ValueError("authorization_id must not be empty")

        with self._lock:
            if authorization_id in self._authorization_ids:
                raise ValueError(
                    TransactionAuthorizationFailure.DUPLICATE_AUTHORIZATION_ID.value
                )
            self._authorization_ids.add(authorization_id)


class TransactionAuthorizationRegistry:
    """Trusted registration and atomic state-update boundary."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._authorizations: dict[str, TransactionAuthorization] = {}
        self._nonces: set[str] = set()

    def register(self, authorization: TransactionAuthorization) -> None:
        authorization_id = authorization.authorization_id
        nonce = authorization.transaction.nonce

        with self._lock:
            if authorization_id in self._authorizations:
                raise ValueError(
                    TransactionAuthorizationFailure.DUPLICATE_AUTHORIZATION_ID.value
                )

            if nonce in self._nonces:
                raise ValueError(
                    TransactionAuthorizationFailure.NONCE_REPLAY.value
                )

            self._authorizations[authorization_id] = authorization
            self._nonces.add(nonce)

    def get(
        self,
        authorization_id: str,
    ) -> TransactionAuthorization | None:
        with self._lock:
            return self._authorizations.get(authorization_id)

    def replace(
        self,
        authorization_id: str,
        expected: TransactionAuthorization,
        replacement: TransactionAuthorization,
    ) -> bool:
        with self._lock:
            current = self._authorizations.get(authorization_id)

            if current is None or current != expected:
                return False

            self._authorizations[authorization_id] = replacement
            return True


class TransactionAuthorizationConsumer:
    """
    Atomic single-use consumption boundary.

    The in-memory lock provides concurrency semantics for this domain
    implementation. Durable multi-process persistence must later provide
    equivalent atomic conditional-update/row-lock semantics.
    """

    def __init__(
        self,
        registry: TransactionAuthorizationRegistry,
    ) -> None:
        self._registry = registry
        self._lock = Lock()

    def consume_once(
        self,
        authorization_id: str,
        *,
        expected_transaction: CanonicalTransaction,
        clock: TrustedClock,
        required_assurance_level: AuthenticationAssuranceLevel = AuthenticationAssuranceLevel.A0,
    ) -> TransactionAuthorizationDecisionResult:
        if not isinstance(
            required_assurance_level,
            AuthenticationAssuranceLevel,
        ):
            return TransactionAuthorizationDecisionResult(
                TransactionAuthorizationDecision.DENY,
                TransactionAuthorizationFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE,
            )

        now = _trusted_now(clock)

        with self._lock:
            authorization = self._registry.get(authorization_id)

            if authorization is None:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_TRANSACTION,
                )

            if (
                authorization.transaction.canonical_representation()
                != expected_transaction.canonical_representation()
            ):
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_TRANSACTION_BINDING,
                )

            if authorization.transaction.principal_id != expected_transaction.principal_id:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_PRINCIPAL_BINDING,
                )

            if authorization.state is TransactionAuthorizationState.CONSUMED:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.ALREADY_CONSUMED,
                )

            if authorization.state is TransactionAuthorizationState.REVOKED:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.REVOKED,
                )

            if authorization.state is TransactionAuthorizationState.EXPIRED:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.EXPIRED,
                )

            if now >= authorization.expires_at:
                expired = transition(
                    authorization,
                    TransactionAuthorizationState.EXPIRED,
                )
                self._registry.replace(
                    authorization_id,
                    authorization,
                    expired,
                )
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.EXPIRED,
                )

            if authorization.state is not TransactionAuthorizationState.APPROVED:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_APPROVAL,
                )

            approval = authorization.approval

            if approval is None:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_APPROVAL,
                )

            if approval.assurance.principal_id != authorization.transaction.principal_id:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_ASSURANCE_PROVENANCE,
                )

            if (
                approval.transaction.canonical_representation()
                != authorization.transaction.canonical_representation()
            ):
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INVALID_TRANSACTION_BINDING,
                )

            if approval.assurance.assurance_level.value < required_assurance_level.value:
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE,
                )

            consumed = transition(
                authorization,
                TransactionAuthorizationState.CONSUMED,
            )

            if not self._registry.replace(
                authorization_id,
                authorization,
                consumed,
            ):
                return TransactionAuthorizationDecisionResult(
                    TransactionAuthorizationDecision.DENY,
                    TransactionAuthorizationFailure.ALREADY_CONSUMED,
                )

            return TransactionAuthorizationDecisionResult(
                TransactionAuthorizationDecision.ALLOW
            )


def transition(
    authorization: TransactionAuthorization,
    new_state: TransactionAuthorizationState,
) -> TransactionAuthorization:
    allowed = _ALLOWED_TRANSITIONS[authorization.state]

    if new_state not in allowed:
        raise ValueError(
            f"invalid transaction authorization transition: "
            f"{authorization.state.value} -> {new_state.value}"
        )

    return TransactionAuthorization(
        authorization_id=authorization.authorization_id,
        transaction=authorization.transaction,
        created_at=authorization.created_at,
        expires_at=authorization.expires_at,
        state=new_state,
        approval=authorization.approval,
    )


def attach_approval(
    authorization: TransactionAuthorization,
    approval: TrustedApprovalEvidence,
    *,
    clock: TrustedClock,
) -> TransactionAuthorization:
    if (
        authorization.state
        is not TransactionAuthorizationState.PENDING_USER_APPROVAL
    ):
        raise ValueError("approval can only be attached while pending")

    if approval.authorization_id != authorization.authorization_id:
        raise ValueError("approval authorization binding mismatch")

    if approval.assurance.principal_id != authorization.transaction.principal_id:
        raise ValueError("approval assurance principal binding mismatch")

    if (
        approval.transaction.canonical_representation()
        != authorization.transaction.canonical_representation()
    ):
        raise ValueError("approval is not bound to the exact transaction")

    now = _trusted_now(clock)

    if approval.approved_at > now:
        raise ValueError("future-dated approval is invalid")

    return transition(
        TransactionAuthorization(
            authorization_id=authorization.authorization_id,
            transaction=authorization.transaction,
            created_at=authorization.created_at,
            expires_at=authorization.expires_at,
            state=TransactionAuthorizationState.PENDING_USER_APPROVAL,
            approval=approval,
        ),
        TransactionAuthorizationState.APPROVED,
    )


def expire_if_due(
    authorization: TransactionAuthorization,
    *,
    clock: TrustedClock,
) -> TransactionAuthorization:
    now = _trusted_now(clock)

    if (
        authorization.state is TransactionAuthorizationState.APPROVED
        and now >= authorization.expires_at
    ):
        return transition(
            authorization,
            TransactionAuthorizationState.EXPIRED,
        )

    return authorization


def consume(
    authorization: TransactionAuthorization,
    *,
    clock: TrustedClock,
    required_assurance_level: AuthenticationAssuranceLevel = AuthenticationAssuranceLevel.A0,
) -> TransactionAuthorizationDecisionResult:
    if not isinstance(
        required_assurance_level,
        AuthenticationAssuranceLevel,
    ):
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE,
        )

    now = _trusted_now(clock)

    if authorization.state is TransactionAuthorizationState.CONSUMED:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.ALREADY_CONSUMED,
        )

    if authorization.state is TransactionAuthorizationState.EXPIRED:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.EXPIRED,
        )

    if authorization.state is TransactionAuthorizationState.REVOKED:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.REVOKED,
        )

    if authorization.state is not TransactionAuthorizationState.APPROVED:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.INVALID_APPROVAL,
        )

    if now >= authorization.expires_at:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.EXPIRED,
        )

    approval = authorization.approval

    if approval is None:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.INVALID_APPROVAL,
        )

    if approval.assurance.principal_id != authorization.transaction.principal_id:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.INVALID_ASSURANCE_PROVENANCE,
        )

    if (
        approval.transaction.canonical_representation()
        != authorization.transaction.canonical_representation()
    ):
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.INVALID_TRANSACTION_BINDING,
        )

    if approval.assurance.assurance_level.value < required_assurance_level.value:
        return TransactionAuthorizationDecisionResult(
            TransactionAuthorizationDecision.DENY,
            TransactionAuthorizationFailure.INSUFFICIENT_AUTHENTICATION_ASSURANCE,
        )

    return TransactionAuthorizationDecisionResult(
        TransactionAuthorizationDecision.ALLOW
    )


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")

    return value.astimezone(timezone.utc)


def _trusted_now(clock: TrustedClock) -> datetime:
    return _normalize_datetime(clock.now())
