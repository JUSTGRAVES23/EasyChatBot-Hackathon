from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.learning.subscription_world_access_service import (
    SubscriptionWorldAccessService,
)
from app.application.payment.entitlement_policy import (
    EntitlementPolicy,
    UnknownEntitlementPlanError,
)
from app.domain.learning.learner_world_access import (
    ADMIN,
    BETA,
    SUBSCRIPTION,
)
from app.domain.learning.world_access_tier import WorldAccessTier


@dataclass(frozen=True)
class FakeWorld:
    identifier: str
    access_tier: WorldAccessTier


class FakeWorldRepository:
    def __init__(self, worlds):
        self.worlds = tuple(worlds)

    def list_all(self):
        return self.worlds


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def worlds():
    return (
        FakeWorld(
            identifier="french",
            access_tier=WorldAccessTier.NORMAL,
        ),
        FakeWorld(
            identifier="french-b1",
            access_tier=WorldAccessTier.PREMIUM,
        ),
        FakeWorld(
            identifier="special-world",
            access_tier=WorldAccessTier.SPECIAL,
        ),
    )


@pytest.fixture
def world_access_service():
    service = AsyncMock()
    return service


@pytest.fixture
def service(worlds, world_access_service):
    return SubscriptionWorldAccessService(
        entitlement_policy=EntitlementPolicy(),
        world_access_service=world_access_service,
        learning_world_repository=FakeWorldRepository(worlds),
    )


@pytest.mark.asyncio
async def test_normal_grants_normal_and_revokes_premium_and_special(
    service,
    world_access_service,
    user_id,
):
    await service.synchronize(
        user_id=user_id,
        plan_code="NORMAL",
        active=True,
    )

    world_access_service.grant_access.assert_awaited_once_with(
        user_id=user_id,
        world_identifier="french",
        access_source=SUBSCRIPTION,
    )

    assert world_access_service.revoke_access.await_count == 2

    revoked_calls = {
        call.kwargs["world_identifier"]
        for call in world_access_service.revoke_access.await_args_list
    }

    assert revoked_calls == {
        "french-b1",
        "special-world",
    }


@pytest.mark.asyncio
async def test_premium_grants_normal_and_premium_but_not_special(
    service,
    world_access_service,
    user_id,
):
    await service.synchronize(
        user_id=user_id,
        plan_code="PREMIUM",
        active=True,
    )

    assert world_access_service.grant_access.await_count == 2

    granted_calls = {
        call.kwargs["world_identifier"]
        for call in world_access_service.grant_access.await_args_list
    }

    assert granted_calls == {
        "french",
        "french-b1",
    }

    world_access_service.revoke_access.assert_awaited_once_with(
        user_id=user_id,
        world_identifier="special-world",
        access_source=SUBSCRIPTION,
    )


@pytest.mark.asyncio
async def test_inactive_subscription_revokes_subscription_access_only(
    service,
    world_access_service,
    user_id,
):
    await service.synchronize(
        user_id=user_id,
        plan_code="PREMIUM",
        active=False,
    )

    assert world_access_service.grant_access.await_count == 0
    assert world_access_service.revoke_access.await_count == 3

    for call in world_access_service.revoke_access.await_args_list:
        assert call.kwargs["user_id"] == user_id
        assert call.kwargs["access_source"] == SUBSCRIPTION


@pytest.mark.asyncio
async def test_beta_and_admin_access_are_never_revoked_directly(
    service,
    world_access_service,
    user_id,
):
    await service.synchronize(
        user_id=user_id,
        plan_code="NORMAL",
        active=True,
    )

    for call in world_access_service.revoke_access.await_args_list:
        assert call.kwargs["access_source"] == SUBSCRIPTION

    assert BETA != SUBSCRIPTION
    assert ADMIN != SUBSCRIPTION


def test_unknown_plan_fails_closed():
    policy = EntitlementPolicy()

    with pytest.raises(
        UnknownEntitlementPlanError,
        match="Unsupported entitlement plan",
    ):
        policy.resolve(
            plan_code="UNKNOWN_PLAN",
            active=True,
        )


def test_inactive_policy_has_no_allowed_tiers():
    policy = EntitlementPolicy()

    resolved = policy.resolve(
        plan_code="PREMIUM",
        active=False,
    )

    assert resolved.active is False
    assert resolved.allowed_world_tiers == frozenset()