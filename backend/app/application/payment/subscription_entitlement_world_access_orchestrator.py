"""Orchestrate subscription entitlement persistence and World access.

This service is the async application boundary between:
    payment entitlement state
        -> Learning World access

It deliberately does not contain Stripe/provider logic.
"""

from __future__ import annotations

from uuid import UUID

from app.application.learning.subscription_world_access_service import (
    SubscriptionWorldAccessService,
)


class SubscriptionEntitlementWorldAccessOrchestrator:
    """Synchronize World access from an authoritative subscription entitlement."""

    def __init__(
        self,
        *,
        subscription_world_access_service: SubscriptionWorldAccessService,
    ) -> None:
        if subscription_world_access_service is None:
            raise ValueError(
                "subscription_world_access_service cannot be None."
            )

        self._subscription_world_access_service = (
            subscription_world_access_service
        )

    async def synchronize(
        self,
        *,
        user_id: UUID,
        plan_code: str,
        active: bool,
    ) -> None:
        """Reconcile World access for the supplied entitlement state.

        The underlying SubscriptionWorldAccessService remains responsible
        for entitlement policy and WorldAccessService authorization.
        """
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        if not isinstance(plan_code, str) or not plan_code.strip():
            raise ValueError("plan_code is required.")

        await self._subscription_world_access_service.synchronize(
            user_id=user_id,
            plan_code=plan_code,
            active=active,
        )


__all__ = ["SubscriptionEntitlementWorldAccessOrchestrator"]