from __future__ import annotations

import pytest

from services.runtime.runtime_application_service import (
    RuntimeApplicationService,
)

from services.external_runtime_service import (
    ExternalRuntimeService,
)

from src.ai_runtime.capabilities.actor_context import RuntimeActorContext

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityResult,
    CapabilityType,
)


class FakeRuntimeGateway:
    """
    Controlled Runtime gateway fake.
    """

    def __init__(self):
        self.last_request = None

    async def execute(
        self,
        request,
    ) -> CapabilityResult:
        """
        Return deterministic Runtime result.
        """

        self.last_request = request

        return CapabilityResult(
            request_id=request.request_id,
            capability=CapabilityType.LIVE_INTELLIGENCE,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "result": "runtime-success",
            },
        )


def create_service() -> RuntimeApplicationService:
    """
    Create RuntimeApplicationService with fake Runtime.
    """

    runtime_service = ExternalRuntimeService(
        gateway=FakeRuntimeGateway(),
    )

    return RuntimeApplicationService(
        runtime_service=runtime_service,
    )


@pytest.mark.asyncio
async def test_runtime_application_service_executes_capability():
    """
    RuntimeApplicationService should create a Runtime request
    and delegate execution.
    """

    service = create_service()

    result = await service.execute(
        capability="live_intelligence",
        payload={
            "query": "latest AI news",
        },
    )

    assert result.status == (
        CapabilityExecutionStatus.COMPLETED
    )

    assert result.capability == (
        CapabilityType.LIVE_INTELLIGENCE
    )

    assert result.output == {
        "result": "runtime-success",
    }

    assert result.request_id is not None


@pytest.mark.asyncio
async def test_runtime_application_service_requires_capability():
    """
    Empty capability should be rejected at the application
    boundary.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Capability cannot be empty",
    ):
        await service.execute(
            capability="",
            payload={},
        )


@pytest.mark.asyncio
async def test_runtime_application_service_requires_payload():
    """
    Missing payload should be rejected.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Payload cannot be None",
    ):
        await service.execute(
            capability="live_intelligence",
            payload=None,
        )


@pytest.mark.asyncio
async def test_runtime_application_service_propagates_actor():
    """
    Authenticated Runtime actor context must be propagated
    into the provider-independent CapabilityRequest.
    """

    gateway = FakeRuntimeGateway()

    runtime_service = ExternalRuntimeService(
        gateway=gateway,
    )

    service = RuntimeApplicationService(
        runtime_service=runtime_service,
    )

    actor = RuntimeActorContext(
        actor_id="user-123",
        roles=frozenset({"ADMIN"}),
    )

    await service.execute(
        capability="internal_data_read",
        payload={
            "operation": "get_beta_user",
            "user_id": "user-123",
        },
        actor=actor,
    )

    assert gateway.last_request is not None
    assert gateway.last_request.actor == actor
    assert gateway.last_request.actor.actor_id == "user-123"
    assert gateway.last_request.actor.roles == frozenset({"ADMIN"})

