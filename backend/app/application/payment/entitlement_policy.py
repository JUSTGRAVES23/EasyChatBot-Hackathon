"""Policy translating subscription plans into Learning World access tiers.

Plans do not map directly to individual Learning Worlds.

Instead:
    subscription plan
        -> entitlement capability
        -> allowed World access tiers

The policy is intentionally provider-neutral and contains no persistence,
Stripe, or WorldAccessService logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.learning.world_access_tier import WorldAccessTier


NORMAL_PLAN = "NORMAL"
PREMIUM_PLAN = "PREMIUM"


@dataclass(frozen=True, slots=True)
class EntitlementAccessPolicy:
    """Resolved World-access capability for one entitlement plan."""

    plan_code: str
    active: bool
    allowed_world_tiers: frozenset[WorldAccessTier]

    def allows_tier(self, tier: WorldAccessTier) -> bool:
        """Return whether the entitlement permits the supplied World tier."""
        if not self.active:
            return False

        return tier in self.allowed_world_tiers


class UnknownEntitlementPlanError(ValueError):
    """Raised when an unknown plan would otherwise fail open."""


class EntitlementPolicy:
    """Canonical plan-to-capability policy.

    Current product policy:

    NORMAL
        -> NORMAL Worlds

    PREMIUM
        -> NORMAL + PREMIUM Worlds

    SPECIAL
        -> never implicitly granted by a subscription plan

    Unknown plans
        -> fail closed

    This class deliberately does not contain individual World identifiers.
    """

    _PLAN_TIERS: dict[str, frozenset[WorldAccessTier]] = {
        NORMAL_PLAN: frozenset(
            {
                WorldAccessTier.NORMAL,
            }
        ),
        PREMIUM_PLAN: frozenset(
            {
                WorldAccessTier.NORMAL,
                WorldAccessTier.PREMIUM,
            }
        ),
    }

    def resolve(
        self,
        *,
        plan_code: str,
        active: bool,
    ) -> EntitlementAccessPolicy:
        if not isinstance(plan_code, str):
            raise ValueError("plan_code must be a string.")

        normalized_plan = plan_code.strip().upper()

        if not normalized_plan:
            raise ValueError("plan_code is required.")

        tiers = self._PLAN_TIERS.get(normalized_plan)

        if tiers is None:
            raise UnknownEntitlementPlanError(
                f"Unsupported entitlement plan: {plan_code!r}."
            )

        return EntitlementAccessPolicy(
            plan_code=normalized_plan,
            active=bool(active),
            allowed_world_tiers=tiers if active else frozenset(),
        )


__all__ = [
    "EntitlementAccessPolicy",
    "EntitlementPolicy",
    "NORMAL_PLAN",
    "PREMIUM_PLAN",
    "UnknownEntitlementPlanError",
]