"""
Tests for Runtime Application Service.

Validates:

Application Layer
        |
        v
RuntimeApplicationService
        |
        v
ExternalRuntimeService
        |
        v
Capability Result

The tests use controlled fakes.

They do not call:

- Parallel API;
- Gemini;
- Google Cloud;
- external providers.
"""

from __future__ import annotations

import pytest

from backend.services.runtime.runtime_application_service import (
    RuntimeApplicationService,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityResult,
    CapabilityType,
)


class FakeRuntimeGateway:
    """
    Controlled Runtime gateway fake.
    """

    async def execute(
        self,
        request,
    ) -> CapabilityResult:
        """
        Return deterministic Runtime result.
        """

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