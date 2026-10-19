from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)


def _build_notification_key(recommendation_id: str) -> str:
    """Build the canonical notification key for one recommendation."""
    recommendation_id = recommendation_id.strip()

    if not recommendation_id:
        raise ValueError(
            "recommendation_id cannot be blank."
        )

    return (
        "platform_intelligence_escalation:"
        f"{recommendation_id}"
    )


class PlatformIntelligenceEscalationDispatchStatus(StrEnum):
    SENT = "SENT"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationDispatchRequest:
    """Authoritative state required before an escalation can be dispatched."""

    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    risk_level: str
    risk_score: float
    quality_gate_status: str
    review_status: str
    decision_status: str
    notification_key: str
    correlation_id: str
    route: str
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (
            self.recommendation_id,
            self.risk_decision_id,
            self.review_item_id,
            self.notification_key,
            self.correlation_id,
            self.route,
            self.risk_level,
            self.quality_gate_status,
            self.review_status,
            self.decision_status,
        )

        if any(
            not isinstance(value, str) or not value.strip()
            for value in required
        ):
            raise ValueError(
                "Required Platform Intelligence dispatch fields "
                "cannot be blank."
            )

        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError(
                "risk_score must be between 0 and 1."
            )

        if any(
            not isinstance(reason, str) or not reason.strip()
            for reason in self.reasons
        ):
            raise ValueError(
                "Dispatch reasons cannot contain blank values."
            )

        expected_notification_key = _build_notification_key(
            self.recommendation_id
        )

        if self.notification_key != expected_notification_key:
            raise ValueError(
                "notification_key must match recommendation_id."
            )


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationDispatchResult:
    status: PlatformIntelligenceEscalationDispatchStatus
    notification_key: str
    provider_message_id: str | None = None
    error_code: str | None = None
    attempt: int | None = None


class PlatformIntelligenceEscalationDispatchService:
    """Revalidate, deduplicate and dispatch one governed escalation."""

    def __init__(
        self,
        *,
        delivery_repository: Any,
        email_workflow: Any,
    ) -> None:
        if delivery_repository is None:
            raise ValueError(
                "delivery_repository cannot be None."
            )

        if email_workflow is None:
            raise ValueError(
                "email_workflow cannot be None."
            )

        self._repository = delivery_repository
        self._email_workflow = email_workflow

    @staticmethod
    def build_notification_key(
        recommendation_id: str,
    ) -> str:
        """Return the canonical recommendation-scoped notification key."""
        return _build_notification_key(recommendation_id)

    async def dispatch(
        self,
        *,
        request: PlatformIntelligenceEscalationDispatchRequest,
        email_request: Any,
        claim_token: str | None = None,
    ) -> PlatformIntelligenceEscalationDispatchResult:
        if claim_token is not None and (
            not isinstance(claim_token, str) or not claim_token.strip()
        ):
            raise ValueError("claim_token must be nonblank when provided.")
        self._revalidate(request)

        existing = await self._repository.get_by_notification_key(
            request.notification_key
        )

        if (
            existing is not None
            and existing.status
            is PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        ):
            return PlatformIntelligenceEscalationDispatchResult(
                status=(
                    PlatformIntelligenceEscalationDispatchStatus
                    .IDEMPOTENT_REPLAY
                ),
                notification_key=existing.notification_key,
                provider_message_id=(
                    existing.provider_message_id
                ),
                attempt=existing.attempt,
            )

        if existing is None:
            try:
                await self._repository.create_started(
                    notification_key=request.notification_key,
                    recommendation_id=request.recommendation_id,
                    risk_decision_id=request.risk_decision_id,
                    review_item_id=request.review_item_id,
                    correlation_id=request.correlation_id,
                )
            except Exception:
                # The durable repository owns the unique-key race.
                # If another worker created the record first, honour
                # the persisted state.
                existing = (
                    await self._repository
                    .get_by_notification_key(
                        request.notification_key
                    )
                )

                if existing is None:
                    raise

        elif (
            existing.status
            is PlatformIntelligenceEscalationDeliveryStatus.FAILED
        ):
            if not claim_token:
                return PlatformIntelligenceEscalationDispatchResult(
                    status=PlatformIntelligenceEscalationDispatchStatus.FAILED,
                    notification_key=request.notification_key,
                    error_code="RETRY_CLAIM_TOKEN_REQUIRED",
                    attempt=existing.attempt,
                )
            await self._repository.start_retry(
                notification_key=request.notification_key,
                claim_token=claim_token,
            )

        elif (
            existing.status
            is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        ):
            # A STARTED record has an ambiguous delivery outcome.
            # Do not resend automatically: the provider may already
            # have accepted the message. Reconciliation is required.
            return PlatformIntelligenceEscalationDispatchResult(
                status=PlatformIntelligenceEscalationDispatchStatus.FAILED,
                notification_key=request.notification_key,
                error_code=(
                    "DELIVERY_OUTCOME_AMBIGUOUS_REQUIRES_RECONCILIATION"
                ),
                attempt=existing.attempt,
            )

        try:
            workflow_result = self._email_workflow.send(
                email_request
            )

            if inspect.isawaitable(workflow_result):
                workflow_result = await workflow_result

            # The current PI email workflow may return its request
            # containing an awaitable `delivery` result.
            #
            # Resolve it before marking the durable delivery as
            # successful so that invocation of the workflow itself
            # cannot be mistaken for successful provider delivery.
            delivery = getattr(
                workflow_result,
                "delivery",
                None,
            )

            if inspect.isawaitable(delivery):
                delivery = await delivery

            provider_message_id = (
                self._extract_provider_message_id(
                    delivery
                    if delivery is not None
                    else workflow_result
                )
            )

        except Exception as exc:
            error_code = self._error_code(exc)

            await self._repository.mark_failed(
                notification_key=request.notification_key,
                error_code=error_code,
                claim_token=claim_token,
            )

            return PlatformIntelligenceEscalationDispatchResult(
                status=(
                    PlatformIntelligenceEscalationDispatchStatus
                    .FAILED
                ),
                notification_key=request.notification_key,
                error_code=error_code,
            )

        await self._repository.mark_succeeded(
            notification_key=request.notification_key,
            provider_message_id=provider_message_id,
            claim_token=claim_token,
        )

        record = (
            await self._repository.get_by_notification_key(
                request.notification_key
            )
        )

        return PlatformIntelligenceEscalationDispatchResult(
            status=(
                PlatformIntelligenceEscalationDispatchStatus
                .SENT
            ),
            notification_key=request.notification_key,
            provider_message_id=provider_message_id,
            attempt=(
                record.attempt
                if record is not None
                else None
            ),
        )

    @staticmethod
    def _revalidate(
        request: PlatformIntelligenceEscalationDispatchRequest,
    ) -> None:
        if request.quality_gate_status != "PASSED":
            raise ValueError(
                "Dispatch blocked: quality gate is not PASSED."
            )

        if request.review_status != "IN_REVIEW":
            raise ValueError(
                "Dispatch blocked: review is not IN_REVIEW."
            )

        if request.decision_status != "PENDING_HUMAN_REVIEW":
            raise ValueError(
                "Dispatch blocked: decision is not "
                "PENDING_HUMAN_REVIEW."
            )

        expected_key = _build_notification_key(
            request.recommendation_id
        )

        if request.notification_key != expected_key:
            raise ValueError(
                "notification_key does not match "
                "recommendation_id."
            )

    @staticmethod
    def _extract_provider_message_id(
        result: object,
    ) -> str | None:
        if isinstance(result, dict):
            value = (
                result.get("provider_message_id")
                or result.get("id")
                or result.get("message_id")
            )

            return (
                str(value)
                if value is not None
                else None
            )

        return None

    @staticmethod
    def _error_code(
        exc: Exception,
    ) -> str:
        explicit = getattr(
            exc,
            "error_code",
            None,
        )

        if (
            isinstance(explicit, str)
            and explicit.strip()
        ):
            return explicit.strip()[:100]

        return type(exc).__name__.upper()[:100]