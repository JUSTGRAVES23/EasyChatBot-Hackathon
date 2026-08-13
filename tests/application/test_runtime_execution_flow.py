"""
Runtime execution vertical slice test.

Validates:

Application
    |
    v
External Runtime Service
    |
    v
Capability Gateway
    |
    v
Capability Executor
    |
    v
Capability Result

The test uses controlled fakes.

It does not call:
- Parallel API
- Gemini
- Google Cloud
- external providers
"""


from __future__ import annotations

import pytest

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


class FakeRuntimeGateway:
    """
    Fake capability gateway.

    Simulates a successful Runtime execution
    without external dependencies.
    """

    async def execute(
        self,
        context: ExecutionContext,
    ):
        return {
            "status": "completed",
            "capability": "live_intelligence",
            "results": [
                {
                    "title": "AI developments 2026",
                    "source": "fake_parallel",
                }
            ],
        }


@pytest.mark.asyncio
async def test_application_runtime_vertical_slice():
    """
    Validate:

    Application
        ->
    External Runtime Service
        ->
    Capability Gateway
        ->
    Result
    """

    gateway = FakeRuntimeGateway()

    service = ExternalRuntimeService(
        gateway=gateway,
    )

    context = ExecutionContext(
        user_id="runtime-test-user",
        request="Find latest AI developments.",
    )

    result = await service.execute(
        context,
    )

    assert result is not None

    assert result["status"] == "completed"

    assert (
        result["capability"]
        == "live_intelligence"
    )

    assert len(
        result["results"]
    ) == 1

    assert (
        result["results"][0]["source"]
        == "fake_parallel"
    )