from uuid import UUID, uuid4

import pytest

from app.application.payment.subscription_entitlement_service import (
    SubscriptionEntitlementResult,
)
from app.application.payment.subscription_entitlement_world_access_bridge import (
    SubscriptionEntitlementWorldAccessBridge,
)


class FakeWorldAccessOrchestrator:
    def __init__(self):
        self.calls = []

    async def synchronize(
        self,
        *,
        user_id: UUID,
        plan_code: str,
        active: bool,
    ):
        self.calls.append(
            {
                "user_id": user_id,
                "plan_code": plan_code,
                "active": active,
            }
        )


@pytest.mark.asyncio
async def test_bridge_forwards_authoritative_entitlement_result():
    orchestrator = FakeWorldAccessOrchestrator()
    bridge = SubscriptionEntitlementWorldAccessBridge(
        orchestrator
    )

    user_id = uuid4()

    result = SubscriptionEntitlementResult(
        beneficiary_user_id=str(user_id),
        plan_code="PREMIUM",
        active=True,
    )

    await bridge.synchronize(result)

    assert orchestrator.calls == [
        {
            "user_id": user_id,
            "plan_code": "PREMIUM",
            "active": True,
        }
    ]


@pytest.mark.asyncio
async def test_bridge_preserves_inactive_entitlement_state():
    orchestrator = FakeWorldAccessOrchestrator()
    bridge = SubscriptionEntitlementWorldAccessBridge(
        orchestrator
    )

    user_id = uuid4()

    result = SubscriptionEntitlementResult(
        beneficiary_user_id=str(user_id),
        plan_code="PREMIUM",
        active=False,
    )

    await bridge.synchronize(result)

    assert orchestrator.calls == [
        {
            "user_id": user_id,
            "plan_code": "PREMIUM",
            "active": False,
        }
    ]


@pytest.mark.asyncio
async def test_bridge_rejects_non_result_input():
    orchestrator = FakeWorldAccessOrchestrator()
    bridge = SubscriptionEntitlementWorldAccessBridge(
        orchestrator
    )

    with pytest.raises(TypeError, match="SubscriptionEntitlementResult"):
        await bridge.synchronize(object())


@pytest.mark.asyncio
async def test_bridge_rejects_empty_user_id():
    orchestrator = FakeWorldAccessOrchestrator()
    bridge = SubscriptionEntitlementWorldAccessBridge(
        orchestrator
    )

    result = SubscriptionEntitlementResult(
        beneficiary_user_id="",
        plan_code="PREMIUM",
        active=True,
    )

    with pytest.raises(
        ValueError,
        match="beneficiary_user_id cannot be empty",
    ):
        await bridge.synchronize(result)

    assert orchestrator.calls == []


@pytest.mark.asyncio
async def test_bridge_rejects_invalid_user_id():
    orchestrator = FakeWorldAccessOrchestrator()
    bridge = SubscriptionEntitlementWorldAccessBridge(
        orchestrator
    )

    result = SubscriptionEntitlementResult(
        beneficiary_user_id="child-001",
        plan_code="PREMIUM",
        active=True,
    )

    with pytest.raises(
        ValueError,
        match="beneficiary_user_id must contain a valid UUID",
    ):
        await bridge.synchronize(result)

    assert orchestrator.calls == []


def test_bridge_requires_orchestrator():
    with pytest.raises(
        ValueError,
        match="orchestrator cannot be None",
    ):
        SubscriptionEntitlementWorldAccessBridge(None)