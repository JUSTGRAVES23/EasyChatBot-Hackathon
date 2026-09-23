"""Provision Learning World access from subscription entitlements."""

from __future__ import annotations

from uuid import UUID

from app.application.payment.entitlement_policy import (
    EntitlementPolicy,
)
from app.application.services.world_access_service import (
    WorldAccessService,
)
from app.domain.learning.learner_world_access import SUBSCRIPTION
from app.domain.learning.world_access_tier import WorldAccessTier


class SubscriptionWorldAccessService:
    """Translate an active subscription entitlement into World access.

    Responsibilities:
    - resolve the plan's access-tier capability;
    - enumerate authoritative Learning Worlds;
    - grant permitted World access through WorldAccessService;
    - revoke subscription-originated access when no longer permitted.

    This service does NOT:
    - call Stripe;
    - persist subscriptions;
    - persist entitlements;
    - create Learning Worlds;
    - map plans to individual World identifiers;
    - delete learning history;
    - revoke Beta/Admin access.

    WorldAccessService remains the canonical authorization boundary.
    """

    def __init__(
        self,
        *,
        entitlement_policy: EntitlementPolicy,
        world_access_service: WorldAccessService,
        learning_world_repository,
    ) -> None:
        if entitlement_policy is None:
            raise ValueError("entitlement_policy cannot be None.")

        if world_access_service is None:
            raise ValueError("world_access_service cannot be None.")

        if learning_world_repository is None:
            raise ValueError(
                "learning_world_repository cannot be None."
            )

        self._entitlement_policy = entitlement_policy
        self._world_access_service = world_access_service
        self._learning_world_repository = learning_world_repository

    async def synchronize(
        self,
        *,
        user_id: UUID,
        plan_code: str,
        active: bool,
    ) -> None:
        """Reconcile subscription-originated World access.

        Active plans:
            NORMAL  -> NORMAL Worlds
            PREMIUM -> NORMAL + PREMIUM Worlds

        Inactive plans:
            subscription-originated NORMAL/PREMIUM access is revoked.

        SPECIAL Worlds are never automatically granted.
        """

        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        policy = self._entitlement_policy.resolve(
            plan_code=plan_code,
            active=active,
        )

        worlds = self._learning_world_repository.list_all()

        for world in worlds:
            tier = self._world_access_tier(world)

            if policy.allows_tier(tier):
                await self._world_access_service.grant_access(
                    user_id=user_id,
                    world_identifier=world.identifier,
                    access_source=SUBSCRIPTION,
                )
                continue

            # Only subscription-originated access may be revoked here.
            # Beta/Admin/other independently granted access is preserved.
            await self._world_access_service.revoke_access(
                user_id=user_id,
                world_identifier=world.identifier,
                access_source=SUBSCRIPTION,
            )

    @staticmethod
    def _world_access_tier(world) -> WorldAccessTier:
        tier = getattr(world, "access_tier", None)

        if not isinstance(tier, WorldAccessTier):
            raise ValueError(
                "Learning World catalogue entry has an invalid "
                "access_tier."
            )

        return tier


__all__ = ["SubscriptionWorldAccessService"]