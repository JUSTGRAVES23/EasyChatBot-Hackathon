from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.payment.subscription_entitlement_world_access_orchestrator import (
    SubscriptionEntitlementWorldAccessOrchestrator,
)


@pytest.mark.asyncio
async def test_synchronize_delegates_authoritative_entitlement_state():
    service = AsyncMock()
    orchestrator = SubscriptionEntitlementWorldAccessOrchestrator(
        subscription_world_access_service=service,
    )

    user_id = uuid4()

    await orchestrator.synchronize(
        user_id=user_id,
        plan_code="PREMIUM",
        active=True,
    )

    service.synchronize.assert_awaited_once_with(
        user_id=user_id,
        plan_code="PREMIUM",
        active=True,
    )


@pytest.mark.asyncio
async def test_inactive_entitlement_is_forwarded_for_revocation():
    service = AsyncMock()
    orchestrator = SubscriptionEntitlementWorldAccessOrchestrator(
        subscription_world_access_service=service,
    )

    user_id = uuid4()

    await orchestrator.synchronize(
        user_id=user_id,
        plan_code="PREMIUM",
        active=False,
    )

    service.synchronize.assert_awaited_once_with(
        user_id=user_id,
        plan_code="PREMIUM",
        active=False,
    )


@pytest.mark.asyncio
async def test_invalid_user_id_is_rejected():
    service = AsyncMock()
    orchestrator = SubscriptionEntitlementWorldAccessOrchestrator(
        subscription_world_access_service=service,
    )

    with pytest.raises(ValueError, match="user_id must be a UUID"):
        await orchestrator.synchronize(
            user_id="child-001",
            plan_code="PREMIUM",
            active=True,
        )


@pytest.mark.asyncio
async def test_empty_plan_code_is_rejected():
    service = AsyncMock()
    orchestrator = SubscriptionEntitlementWorldAccessOrchestrator(
        subscription_world_access_service=service,
    )

    with pytest.raises(ValueError, match="plan_code is required"):
        await orchestrator.synchronize(
            user_id=uuid4(),
            plan_code="",
            active=True,
        )