
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import FrozenSet

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryRecord,
    PlatformIntelligenceEscalationDeliveryStatus,
)


class PlatformIntelligenceEscalationRetryPolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"


class PlatformIntelligenceEscalationRetryDecision(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationRetryPolicy:
    """Versioned, explicitly approved retry policy for PI escalation delivery."""

    policy_id: str
    policy_version: str
    status: PlatformIntelligenceEscalationRetryPolicyStatus
    max_attempts: int
    base_backoff_seconds: int
    max_backoff_seconds: int
    retryable_error_codes: FrozenSet[str]
    retry_interrupted_started: bool = True

    def __post_init__(self) -> None:
        required = (self.policy_id, self.policy_version)

        if any(
            not isinstance(value, str) or not value.strip()
            for value in required
        ):
            raise ValueError(
                "policy_id and policy_version cannot be blank."
            )

        if self.max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1."
            )

        if self.base_backoff_seconds < 0:
            raise ValueError(
                "base_backoff_seconds cannot be negative."
            )

        if self.max_backoff_seconds < self.base_backoff_seconds:
            raise ValueError(
                "max_backoff_seconds cannot be lower than "
                "base_backoff_seconds."
            )

        if any(
            not isinstance(code, str) or not code.strip()
            for code in self.retryable_error_codes
        ):
            raise ValueError(
                "retryable_error_codes cannot contain blank values."
            )


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationRetryResult:
    """Deterministic retry eligibility decision and policy-derived timing."""

    decision: PlatformIntelligenceEscalationRetryDecision
    notification_key: str
    attempt: int
    policy_id: str
    policy_version: str
    reason: str
    next_eligible_at: datetime | None = None
    backoff_seconds: int | None = None


class PlatformIntelligenceEscalationRetryPolicyService:
    """Evaluate whether a durable PI delivery record may be retried.

    This service is side-effect free.

    It does not:
    - mutate delivery state;
    - call an email provider;
    - schedule work;
    - read the wall clock.

    The caller supplies the reference time used for the eligibility decision.
    The delivery record supplies the authoritative timestamp from which the
    retry backoff is calculated.
    """

    def __init__(
        self,
        *,
        policy: PlatformIntelligenceEscalationRetryPolicy,
    ) -> None:
        if policy is None:
            raise ValueError("policy cannot be None.")

        self._policy = policy

    @property
    def policy(self) -> PlatformIntelligenceEscalationRetryPolicy:
        return self._policy

    def evaluate(
        self,
        *,
        record: PlatformIntelligenceEscalationDeliveryRecord,
        reference_at: datetime,
    ) -> PlatformIntelligenceEscalationRetryResult:
        self._validate_reference_time(reference_at)

        if not record.notification_key.strip():
            raise ValueError(
                "notification_key cannot be blank."
            )

        if record.attempt < 1:
            raise ValueError(
                "delivery attempt must be at least 1."
            )

        if (
            self._policy.status
            is not PlatformIntelligenceEscalationRetryPolicyStatus.APPROVED
        ):
            return self._result(
                record=record,
                decision=(
                    PlatformIntelligenceEscalationRetryDecision
                    .NOT_ELIGIBLE
                ),
                reason="Retry policy is not APPROVED.",
            )

        if (
            record.status
            is PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        ):
            return self._result(
                record=record,
                decision=(
                    PlatformIntelligenceEscalationRetryDecision
                    .NOT_ELIGIBLE
                ),
                reason="Delivery already SUCCEEDED.",
            )

        if record.attempt >= self._policy.max_attempts:
            return self._result(
                record=record,
                decision=(
                    PlatformIntelligenceEscalationRetryDecision
                    .NOT_ELIGIBLE
                ),
                reason="Maximum delivery attempts reached.",
            )

        if (
            record.status
            is PlatformIntelligenceEscalationDeliveryStatus.FAILED
        ):
            if not record.error_code:
                return self._result(
                    record=record,
                    decision=(
                        PlatformIntelligenceEscalationRetryDecision
                        .NOT_ELIGIBLE
                    ),
                    reason=(
                        "FAILED delivery has no error code for retry "
                        "classification."
                    ),
                )

            if (
                record.error_code
                not in self._policy.retryable_error_codes
            ):
                return self._result(
                    record=record,
                    decision=(
                        PlatformIntelligenceEscalationRetryDecision
                        .NOT_ELIGIBLE
                    ),
                    reason=(
                        f"Error code {record.error_code!r} "
                        "is not retryable."
                    ),
                )

            return self._eligible_result(
                record=record,
                reference_at=reference_at,
            )

        if (
            record.status
            is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        ):
            if not self._policy.retry_interrupted_started:
                return self._result(
                    record=record,
                    decision=(
                        PlatformIntelligenceEscalationRetryDecision
                        .NOT_ELIGIBLE
                    ),
                    reason=(
                        "Interrupted STARTED deliveries are not "
                        "retryable by policy."
                    ),
                )

            # STARTED represents recovery of an interrupted attempt.
            # Recovery does NOT increment the attempt, but it remains
            # subject to the same policy-controlled backoff.
            return self._eligible_result(
                record=record,
                reference_at=reference_at,
            )

        return self._result(
            record=record,
            decision=(
                PlatformIntelligenceEscalationRetryDecision
                .NOT_ELIGIBLE
            ),
            reason=(
                f"Delivery status {record.status.value!r} "
                "is not retryable."
            ),
        )

    def backoff_seconds(self, *, attempt: int) -> int:
        """Return deterministic exponential backoff for the retry.

        Attempt 1:
            base_backoff_seconds

        Attempt 2:
            base_backoff_seconds * 2

        Attempt 3:
            base_backoff_seconds * 4

        The result is capped at max_backoff_seconds.
        """
        if attempt < 1:
            raise ValueError(
                "attempt must be at least 1."
            )

        multiplier = 2 ** (attempt - 1)

        return min(
            self._policy.base_backoff_seconds * multiplier,
            self._policy.max_backoff_seconds,
        )

    def _eligible_result(
        self,
        *,
        record: PlatformIntelligenceEscalationDeliveryRecord,
        reference_at: datetime,
    ) -> PlatformIntelligenceEscalationRetryResult:
        delay = self.backoff_seconds(
            attempt=record.attempt
        )

        # The backoff is calculated from the persisted delivery timestamp,
        # not from the caller's current reference time.
        #
        # This is essential for deterministic due/not-due evaluation.
        if record.updated_at is None:
            return self._result(
                record=record,
                decision=(
                    PlatformIntelligenceEscalationRetryDecision
                    .NOT_ELIGIBLE
                ),
                reason=(
                    "Delivery record has no updated_at timestamp "
                    "from which retry timing can be established."
                ),
            )

        self._validate_timestamp(
            record.updated_at,
            field_name="record.updated_at",
        )

        next_eligible_at = (
            record.updated_at
            + timedelta(seconds=delay)
        )

        # The retry backoff must have elapsed before the delivery
        # becomes eligible for another attempt.
        if reference_at < next_eligible_at:
            return self._result(
                record=record,
                decision=(
                    PlatformIntelligenceEscalationRetryDecision
                    .NOT_ELIGIBLE
                ),
                reason=(
                    "Delivery is not yet eligible because the "
                    "policy-derived backoff window has not elapsed."
                ),
                next_eligible_at=next_eligible_at,
                backoff_seconds=delay,
            )

        # reference_at is exactly at or after next_eligible_at.
        return self._result(
            record=record,
            decision=(
                PlatformIntelligenceEscalationRetryDecision
                .ELIGIBLE
            ),
            reason=(
                "Delivery is eligible for a policy-controlled retry."
            ),
            next_eligible_at=next_eligible_at,
            backoff_seconds=delay,
        )

    def _result(
        self,
        *,
        record: PlatformIntelligenceEscalationDeliveryRecord,
        decision: PlatformIntelligenceEscalationRetryDecision,
        reason: str,
        next_eligible_at: datetime | None = None,
        backoff_seconds: int | None = None,
    ) -> PlatformIntelligenceEscalationRetryResult:
        return PlatformIntelligenceEscalationRetryResult(
            decision=decision,
            notification_key=record.notification_key,
            attempt=record.attempt,
            policy_id=self._policy.policy_id,
            policy_version=self._policy.policy_version,
            reason=reason,
            next_eligible_at=next_eligible_at,
            backoff_seconds=backoff_seconds,
        )

    @staticmethod
    def _validate_reference_time(
        reference_at: datetime,
    ) -> None:
        if (
            reference_at.tzinfo is None
            or reference_at.utcoffset() is None
        ):
            raise ValueError(
                "reference_at must be timezone-aware."
            )

    @staticmethod
    def _validate_timestamp(
        value: datetime,
        *,
        field_name: str,
    ) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                f"{field_name} must be timezone-aware."
            )
