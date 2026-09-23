from __future__ import annotations

import pytest

from app.application.payment.entitlement_policy import (
    NORMAL_PLAN,
    PREMIUM_PLAN,
    EntitlementPolicy,
    UnknownEntitlementPlanError,
)
from app.domain.learning.world_access_tier import WorldAccessTier


def test_normal_plan_allows_only_normal_worlds():
    policy = EntitlementPolicy()

    result = policy.resolve(
        plan_code=NORMAL_PLAN,
        active=True,
    )

    assert result.plan_code == NORMAL_PLAN
    assert result.active is True
    assert result.allowed_world_tiers == frozenset(
        {
            WorldAccessTier.NORMAL,
        }
    )

    assert result.allows_tier(WorldAccessTier.NORMAL)
    assert not result.allows_tier(WorldAccessTier.PREMIUM)
    assert not result.allows_tier(WorldAccessTier.SPECIAL)


def test_premium_plan_includes_normal_and_premium():
    policy = EntitlementPolicy()

    result = policy.resolve(
        plan_code=PREMIUM_PLAN,
        active=True,
    )

    assert result.plan_code == PREMIUM_PLAN
    assert result.active is True
    assert result.allowed_world_tiers == frozenset(
        {
            WorldAccessTier.NORMAL,
            WorldAccessTier.PREMIUM,
        }
    )

    assert result.allows_tier(WorldAccessTier.NORMAL)
    assert result.allows_tier(WorldAccessTier.PREMIUM)
    assert not result.allows_tier(WorldAccessTier.SPECIAL)


@pytest.mark.parametrize(
    "plan_code",
    [
        "UNKNOWN",
        "PREMIUM_MONTHLY",
        "SPECIAL",
    ],
)
def test_unknown_or_noncanonical_plan_fails_closed(plan_code):
    policy = EntitlementPolicy()

    with pytest.raises(UnknownEntitlementPlanError):
        policy.resolve(
            plan_code=plan_code,
            active=True,
        )


def test_empty_plan_code_is_rejected():
    policy = EntitlementPolicy()

    with pytest.raises(
        ValueError,
        match="plan_code is required",
    ):
        policy.resolve(
            plan_code="",
            active=True,
        )


def test_plan_code_is_normalized():
    policy = EntitlementPolicy()

    result = policy.resolve(
        plan_code=" premium ",
        active=True,
    )

    assert result.plan_code == PREMIUM_PLAN
    assert result.allows_tier(WorldAccessTier.PREMIUM)


def test_inactive_premium_has_no_access_capability():
    policy = EntitlementPolicy()

    result = policy.resolve(
        plan_code=PREMIUM_PLAN,
        active=False,
    )

    assert result.active is False
    assert result.allowed_world_tiers == frozenset()

    assert not result.allows_tier(WorldAccessTier.NORMAL)
    assert not result.allows_tier(WorldAccessTier.PREMIUM)