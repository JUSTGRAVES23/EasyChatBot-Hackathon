"""
Tests for the AI Runtime Capability Gateway.
"""

import pytest

from src.ai_runtime.capabilities.errors import (
    CapabilityExecutionError,
    CapabilityGovernanceError,
)

from src.ai_runtime.capabilities.executor import (
    CapabilityExecutor,
)

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)

from src.ai_runtime.capabilities.registry import (
    CapabilityRegistry,
)


class FakeGovernanceResult:
    """
    Minimal governance result for gateway tests.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:
        self.allowed = allowed


class FakeGovernance:
    """
    Deterministic governance implementation for tests.
    """

    def __init__(
        self,
        allowed: bool,
    ) -> None:
        self.allowed = allowed
        self.calls = 0

    def evaluate(
        self,
        request: CapabilityRequest,
    ) -> FakeGovernanceResult:

        self.calls += 1

        return FakeGovernanceResult(
            allowed=self.allowed
        )


class FailingGovernance:
    """
    Governance implementation that fails unexpectedly.
    """

    def evaluate(
        self,
        request: CapabilityRequest,
    ) -> FakeGovernanceResult:

        raise RuntimeError(
            "governance infrastructure failure"
        )


class FakeExecutor(CapabilityExecutor):
    """
    Fake executor used to verify gateway orchestration.
    """

    def __init__(self) -> None:
        self.calls = 0
        self.last_request: CapabilityRequest | None = None

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.LIVE_INTELLIGENCE

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:

        self.calls += 1
        self.last_request = request

        return CapabilityResult(
            request_id=request.request_id,
            capability=request.capability,
            status=CapabilityExecutionStatus.COMPLETED,
            output={
                "executed": True,
            },
        )


class FailingExecutor(CapabilityExecutor):
    """
    Executor that fails unexpectedly.
    """

    @property
    def capability(self) -> CapabilityType:
        return CapabilityType.LIVE_INTELLIGENCE

    async def execute(
        self,
        request: CapabilityRequest,
    ) -> CapabilityResult:

        raise RuntimeError(
            "provider failure"
        )


@pytest.mark.asyncio
async def test_gateway_executes_allowed_capability():

    executor = FakeExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    governance = FakeGovernance(
        allowed=True
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=governance,
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="gateway-001",
        payload={
            "topic": "AI Act",
        },
    )

    result = await gateway.execute(
        request
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert governance.calls == 1

    assert executor.calls == 1

    assert executor.last_request is request


@pytest.mark.asyncio
async def test_gateway_rejects_blocked_capability():

    executor = FakeExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    governance = FakeGovernance(
        allowed=False
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=governance,
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="gateway-002",
        payload={
            "topic": "AI Act",
        },
    )

    result = await gateway.execute(
        request
    )

    assert (
        result.status
        == CapabilityExecutionStatus.REJECTED
    )

    assert result.rejected is True

    assert executor.calls == 0

    assert governance.calls == 1

    assert (
        result.metadata["governance_decision"]
        == "rejected"
    )


@pytest.mark.asyncio
async def test_gateway_passes_original_request_to_executor():

    executor = FakeExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    governance = FakeGovernance(
        allowed=True
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=governance,
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="gateway-003",
        payload={
            "topic": "European AI regulation",
            "language": "French",
        },
        metadata={
            "trace_id": "trace-003",
        },
        requested_by="learning_application",
    )

    await gateway.execute(
        request
    )

    assert executor.last_request is request

    assert (
        executor.last_request.payload["language"]
        == "French"
    )

    assert (
        executor.last_request.metadata["trace_id"]
        == "trace-003"
    )


@pytest.mark.asyncio
async def test_governance_is_evaluated_before_execution():

    executor = FakeExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    governance = FakeGovernance(
        allowed=False
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=governance,
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="gateway-004",
        payload={},
    )

    result = await gateway.execute(
        request
    )

    assert result.rejected is True

    assert governance.calls == 1

    assert executor.calls == 0


@pytest.mark.asyncio
async def test_gateway_wraps_governance_failure():

    executor = FakeExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=FailingGovernance(),
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="gateway-error-001",
        payload={
            "topic": "AI Act",
        },
    )

    with pytest.raises(
        CapabilityGovernanceError,
        match="Governance evaluation failed",
    ):
        await gateway.execute(request)

    assert executor.calls == 0


@pytest.mark.asyncio
async def test_gateway_wraps_executor_failure():

    executor = FailingExecutor()

    registry = CapabilityRegistry(
        executors=[executor]
    )

    gateway = CapabilityGateway(
        registry=registry,
        governance=FakeGovernance(
            allowed=True
        ),
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="gateway-error-002",
        payload={
            "topic": "AI Act",
        },
    )

    with pytest.raises(
        CapabilityExecutionError,
        match="Capability executor failed",
    ):
        await gateway.execute(request)