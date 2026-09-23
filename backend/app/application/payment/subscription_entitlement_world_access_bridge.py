from __future__ import annotations

from uuid import UUID

from app.application.payment.subscription_entitlement_service import (
    SubscriptionEntitlementResult,
)
from app.application.payment.subscription_entitlement_world_access_orchestrator import (
    SubscriptionEntitlementWorldAccessOrchestrator,
)


class SubscriptionEntitlementWorldAccessBridge:
    """Bridge persisted subscription entitlement results to World access.

    This is an application-layer boundary between the synchronous payment
    entitlement pipeline and the existing asynchronous World-access
    orchestrator.

    Responsibilities:
    - validate the entitlement result;
    - convert the canonical beneficiary identifier to UUID;
    - delegate to the existing World-access orchestrator.

    This bridge deliberately does not:
    - call Stripe;
    - persist subscriptions or entitlements;
    - implement World-access policy;
    - resolve individual Worlds;
    - create background tasks;
    - schedule work;
    - duplicate World-access orchestration.
    """

    def __init__(
        self,
        orchestrator: SubscriptionEntitlementWorldAccessOrchestrator,
    ) -> None:
        if orchestrator is None:
            raise ValueError("orchestrator cannot be None.")

        self._orchestrator = orchestrator

    async def synchronize(
        self,
        result: SubscriptionEntitlementResult,
    ) -> None:
        """Forward an authoritative entitlement result to World access."""

        if not isinstance(result, SubscriptionEntitlementResult):
            raise TypeError(
                "result must be a SubscriptionEntitlementResult."
            )

        beneficiary_user_id = self._parse_user_id(
            result.beneficiary_user_id
        )

        await self._orchestrator.synchronize(
            user_id=beneficiary_user_id,
            plan_code=result.plan_code,
            active=result.active,
        )

    @staticmethod
    def _parse_user_id(value: str) -> UUID:
        if not isinstance(value, str):
            raise ValueError(
                "beneficiary_user_id must be a UUID string."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "beneficiary_user_id cannot be empty."
            )

        try:
            return UUID(normalized)
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                "beneficiary_user_id must contain a valid UUID."
            ) from exc


__all__ = ["SubscriptionEntitlementWorldAccessBridge"]