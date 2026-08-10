"""
Tests for the Runtime Live Intelligence executor adapter.
"""

import pytest

from src.ai_runtime.capabilities.live_intelligence_executor import (
    LiveIntelligenceExecutor,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)


class FakeLiveIntelligenceAgent:
    """
    Fake implementation of the existing agent contract.
    """

    def __init__(self) -> None:
        self.calls = 0
        self.last_request = None

    async def execute(
        self,
        request,
    ):
        self.calls += 1
        self.last_request = request

        return {
            "topic": request.topic,
            "language": request.language,
            "learner_level": request.learner_level,
            "summary": "AI Act learning content",
        }


def test_executor_declares_live_intelligence():

    executor = LiveIntelligenceExecutor(
        agent=FakeLiveIntelligenceAgent()
    )

    assert (
        executor.capability
        == CapabilityType.LIVE_INTELLIGENCE
    )


@pytest.mark.asyncio
async def test_executor_translates_runtime_request():

    agent = FakeLiveIntelligenceAgent()

    executor = LiveIntelligenceExecutor(
        agent=agent
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="live-runtime-001",
        payload={
            "topic": "AI Act",
            "language": "French",
            "learner_level": "B2",
        },
    )

    result = await executor.execute(
        request
    )

    assert (
        result.status
        == CapabilityExecutionStatus.COMPLETED
    )

    assert result.succeeded is True

    assert agent.calls == 1

    assert agent.last_request.topic == "AI Act"

    assert (
        agent.last_request.language
        == "French"
    )

    assert (
        agent.last_request.learner_level
        == "B2"
    )


@pytest.mark.asyncio
async def test_executor_applies_default_language_and_level():

    agent = FakeLiveIntelligenceAgent()

    executor = LiveIntelligenceExecutor(
        agent=agent
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="live-runtime-002",
        payload={
            "topic": "AI Act",
        },
    )

    result = await executor.execute(
        request
    )

    assert result.succeeded is True

    assert (
        agent.last_request.language
        == "French"
    )

    assert (
        agent.last_request.learner_level
        == "B2"
    )


@pytest.mark.asyncio
async def test_executor_returns_agent_output():

    agent = FakeLiveIntelligenceAgent()

    executor = LiveIntelligenceExecutor(
        agent=agent
    )

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="live-runtime-003",
        payload={
            "topic": "European AI regulation",
        },
    )

    result = await executor.execute(
        request
    )

    assert result.output == {
        "topic": "European AI regulation",
        "language": "French",
        "learner_level": "B2",
        "summary": "AI Act learning content",
    }

    assert (
        result.metadata["executor"]
        == "live_intelligence_executor"
    )


@pytest.mark.asyncio
async def test_executor_rejects_wrong_capability():

    agent = FakeLiveIntelligenceAgent()

    executor = LiveIntelligenceExecutor(
        agent=agent
    )

    request = CapabilityRequest(
        capability=CapabilityType.EVALUATION,
        request_id="live-runtime-004",
        payload={},
    )

    with pytest.raises(
        ValueError,
        match="unsupported capability",
    ):
        await executor.execute(request)

    assert agent.calls == 0


def test_executor_requires_topic():

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="live-runtime-005",
        payload={},
    )

    with pytest.raises(
        ValueError,
        match="requires a string 'topic'",
    ):
        LiveIntelligenceExecutor._build_agent_request(
            request
        )


def test_executor_rejects_non_string_topic():

    request = CapabilityRequest(
        capability=CapabilityType.LIVE_INTELLIGENCE,
        request_id="live-runtime-006",
        payload={
            "topic": 123,
        },
    )

    with pytest.raises(
        ValueError,
        match="requires a string 'topic'",
    ):
        LiveIntelligenceExecutor._build_agent_request(
            request
        )