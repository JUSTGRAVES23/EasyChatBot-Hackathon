"""
Tests for Live Intelligence Agent Handler.
"""

import pytest

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
)


class FakeSearchProvider:
    async def search(
        self,
        query: str,
        max_results: int = 5,
    ):
        return []


class FakeProcessor:
    async def summarise(
        self,
        results,
        language,
        learner_level,
    ):
        return (
            "AI Act summary",
            ["regulation", "governance"],
        )


@pytest.mark.asyncio
async def test_live_intelligence_agent_execution():

    agent = LiveIntelligenceAgent(
        search_provider=FakeSearchProvider(),
        processor=FakeProcessor(),
    )

    result = await agent.execute(
        LiveIntelligenceRequest(
            topic="AI Act updates"
        )
    )

    assert result.topic == "AI Act updates"
    assert result.summary == "AI Act summary"
    assert "governance" in result.key_information


@pytest.mark.asyncio
async def test_live_intelligence_agent_rejects_empty_topic():

    agent = LiveIntelligenceAgent(
        search_provider=FakeSearchProvider(),
        processor=FakeProcessor(),
    )

    with pytest.raises(ValueError):
        await agent.execute(
            LiveIntelligenceRequest(
                topic=""
            )
        )