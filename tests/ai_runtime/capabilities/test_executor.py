"""
Tests for the AI Runtime capability executor contract.
"""

import pytest

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)


class FakeCapabilityExecutor(CapabilityExecutor):
    """
    Minimal executor used only to verify the contract.
    """

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.LIVE_INTELLIGENCE

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "executed": True,
            },
        )


def test_executor_declares_capability():

    executor = FakeCapabilityExecutor()

    assert (
        executor.capability
        == CapabilityType.LIVE_INTELLIGENCE
    )


@pytest.mark.asyncio
async def test_executor_returns_provider_independent_result():

    executor = FakeCapabilityExecutor()

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="req-executor-001",
        payload={
            "topic": "AI Act",
        },
    )

    result = await executor.execute(request)

    assert isinstance(
        result,
        CapabilityResult,
    )

    assert (
        result.request_id
        == "req-executor-001"
    )

    assert (
        result.capability
        == CapabilityType.LIVE_INTELLIGENCE
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.output == {
        "executed": True,
    }


def test_executor_is_abstract():

    with pytest.raises(TypeError):

        CapabilityExecutor()