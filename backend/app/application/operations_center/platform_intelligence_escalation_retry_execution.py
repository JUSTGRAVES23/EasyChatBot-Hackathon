
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_dispatch import (
    PlatformIntelligenceEscalationDispatchRequest,
    PlatformIntelligenceEscalationDispatchResult,
    PlatformIntelligenceEscalationDispatchService,
)
from app.application.operations_center.platform_intelligence_escalation_retry import (
    PlatformIntelligenceEscalationRetryDecision,
    PlatformIntelligenceEscalationRetryPolicyService,
)


class PlatformIntelligenceEscalationRetryExecutionStatus(StrEnum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NOT_DUE = "NOT_DUE"
    RETRIED = "RETRIED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationRetryExecutionResult:
    status: PlatformIntelligenceEscalationRetryExecutionStatus
    notification_key: str
    attempt: int
    reason: str
    dispatch_result: PlatformIntelligenceEscalationDispatchResult | None = None


class PlatformIntelligenceEscalationRetryExecutionService:
    """Execute one policy-authorized retry without owning scheduling.

    This service:
    - retrieves the authoritative durable delivery record;
    - evaluates retry policy;
    - translates the canonical policy decision into an execution outcome;
    - increments FAILED attempts only through the repository;
    - preserves the attempt number for STARTED recovery;
    - delegates actual delivery to the existing dispatch service.

    It does not:
    - schedule future work;
    - sleep;
    - call an email provider directly;
    - mutate delivery state directly;
    - duplicate retry-policy eligibility logic.
    """

    def __init__(
        self,
        *,
        delivery_repository: object,
        retry_policy: PlatformIntelligenceEscalationRetryPolicyService,
        dispatch_service: PlatformIntelligenceEscalationDispatchService,
    ) -> None:
        if delivery_repository is None:
            raise ValueError("delivery_repository cannot be None.")

        if retry_policy is None:
            raise ValueError("retry_policy cannot be None.")

        if dispatch_service is None:
            raise ValueError("dispatch_service cannot be None.")

        self._repository = delivery_repository
        self._retry_policy = retry_policy
        self._dispatch_service = dispatch_service

    async def retry(
        self,
        *,
        request: PlatformIntelligenceEscalationDispatchRequest,
        email_request: object,
        reference_at: datetime,
    ) -> PlatformIntelligenceEscalationRetryExecutionResult:
        record = await self._repository.get_by_notification_key(
            request.notification_key
        )

        if record is None:
            raise ValueError(
                "Retry requires an existing durable delivery record."
            )

        if record.notification_key != request.notification_key:
            raise ValueError(
                "Delivery record notification key does not match request."
            )

        policy_result = self._retry_policy.evaluate(
            record=record,
            reference_at=reference_at,
        )

        if (
            policy_result.decision
            is PlatformIntelligenceEscalationRetryDecision.NOT_ELIGIBLE
        ):
            if policy_result.next_eligible_at is not None:
                return PlatformIntelligenceEscalationRetryExecutionResult(
                    status=(
                        PlatformIntelligenceEscalationRetryExecutionStatus
                        .NOT_DUE
                    ),
                    notification_key=record.notification_key,
                    attempt=record.attempt,
                    reason=policy_result.reason,
                )

            return PlatformIntelligenceEscalationRetryExecutionResult(
                status=(
                    PlatformIntelligenceEscalationRetryExecutionStatus
                    .NOT_ELIGIBLE
                ),
                notification_key=record.notification_key,
                attempt=record.attempt,
                reason=policy_result.reason,
            )

        if (
            policy_result.decision
            is not PlatformIntelligenceEscalationRetryDecision.ELIGIBLE
        ):
            return PlatformIntelligenceEscalationRetryExecutionResult(
                status=(
                    PlatformIntelligenceEscalationRetryExecutionStatus
                    .NOT_ELIGIBLE
                ),
                notification_key=record.notification_key,
                attempt=record.attempt,
                reason=policy_result.reason,
            )

        if (
            record.status
            is PlatformIntelligenceEscalationDeliveryStatus.FAILED
        ):
            await self._repository.start_retry(
                notification_key=record.notification_key,
            )

        # STARTED recovery deliberately does not call start_retry().
        # The durable attempt remains the same because this is recovery
        # of the interrupted attempt rather than a new FAILED retry.
        dispatch_result = await self._dispatch_service.dispatch(
            request=request,
            email_request=email_request,
        )

        return PlatformIntelligenceEscalationRetryExecutionResult(
            status=PlatformIntelligenceEscalationRetryExecutionStatus.RETRIED,
            notification_key=record.notification_key,
            attempt=(
                dispatch_result.attempt
                if dispatch_result.attempt is not None
                else record.attempt
            ),
            reason=policy_result.reason,
            dispatch_result=dispatch_result,
        )
