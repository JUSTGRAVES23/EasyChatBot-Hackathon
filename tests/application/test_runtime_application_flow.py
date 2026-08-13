"""
Runtime Application Service tests.

Validates the application boundary:

RuntimeApplicationService
        |
        v
ExternalRuntimeService
        |
        v
CapabilityGateway

The tests use controlled fakes.

They do not call:

- Parallel Search
- Gemini
- Google Cloud
- external providers
"""


from __future__ import annotations


import pytest


from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from backend.services.runtime.runtime_application_service import (
    RuntimeApplicationService,
)


class FakeRuntimeGateway:
    """
    Controlled Runtime gateway.
    """

    async def execute(
        self,
        request,
    ):
        return {
            "request_id": "runtime-service-test",
            "capability": request.capability,
            "status": "completed",
            "output": {
                "source": "fake-runtime",
            },
        }


@pytest.fixture
def runtime_application_service():
    """
    Create RuntimeApplicationService
    with controlled Runtime dependency.
    """

    external_service = ExternalRuntimeService(
        gateway=FakeRuntimeGateway(),
    )

    return RuntimeApplicationService(
        runtime_service=external_service,
    )


@pytest.mark.asyncio
async def test_runtime_application_service_executes_capability(
    runtime_application_service,
):
    """
    RuntimeApplicationService delegates execution
    to ExternalRuntimeService.
    """

    result = await runtime_application_service.execute(
        capability="live_intelligence",
        payload={
            "query": "AI news",
        },
    )

    assert result["status"] == "completed"
    assert result["capability"] == "live_intelligence"
    assert result["output"]["source"] == "fake-runtime"


@pytest.mark.asyncio
async def test_runtime_application_service_requires_capability(
    runtime_application_service,
):
    """
    Invalid capability input should fail at
    application boundary.
    """

    with pytest.raises(ValueError):
        await runtime_application_service.execute(
            capability="",
            payload={},
        )