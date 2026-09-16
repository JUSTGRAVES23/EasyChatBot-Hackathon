import pytest

from agents.research_agent import (
    ResearchAgent,
)

from intelligence.intelligence_context import (
    IntelligenceContext,
    IntelligenceSource,
)

from providers.provider_result import (
    ProviderResult,
)

from runtime.context.execution_context import (
    ExecutionContext,
)


class FakeResearchProvider:
    """
    Fake research provider used for unit testing.

    This keeps the test independent from the real
    Parallel Search API.
    """

    async def execute(
        self,
        context,
    ):
        return ProviderResult(
            success=True,
            provider_id="fake_research",
            output={
                "query": context.request,
                "results": {
                    "results": [
                        {
                            "title": "European AI Regulation",
                            "url": "https://example.com/ai",
                            "excerpts": [
                                "Current regulatory information."
                            ],
                        }
                    ]
                },
            },
        )


@pytest.mark.asyncio
async def test_research_agent_returns_intelligence_context():

    agent = ResearchAgent(
        provider=FakeResearchProvider()
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Latest European AI regulation",
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert result.agent_id == (
        "research_agent"
    )

    assert isinstance(
        result.output,
        IntelligenceContext,
    )

    assert result.output.query == (
        "Latest European AI regulation"
    )

    assert result.output.source_count == 1

    assert isinstance(
        result.output.sources[0],
        IntelligenceSource,
    )

    assert result.output.sources[0].title == (
        "European AI Regulation"
    )

    assert result.output.sources[0].url == (
        "https://example.com/ai"
    )

    assert (
        result.output.sources[0].content
        == "Current regulatory information."
    )


@pytest.mark.asyncio
async def test_research_agent_propagates_provider_failure():

    class FailingResearchProvider:
        """
        Fake provider representing a provider failure.
        """

        async def execute(
            self,
            context,
        ):
            return ProviderResult(
                success=False,
                provider_id="fake_research",
                output=None,
                error="Research provider unavailable",
            )

    agent = ResearchAgent(
        provider=FailingResearchProvider()
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="Latest European AI regulation",
    )

    result = await agent.execute(
        context
    )

    assert result.success is False

    assert result.agent_id == (
        "research_agent"
    )

    assert result.output is None

    assert result.error == (
        "Research provider unavailable"
    )


@pytest.mark.asyncio
async def test_research_agent_handles_empty_results():

    class EmptyResearchProvider:
        """
        Fake provider returning no research results.
        """

        async def execute(
            self,
            context,
        ):
            return ProviderResult(
                success=True,
                provider_id="fake_research",
                output={
                    "query": context.request,
                    "results": {
                        "results": []
                    },
                },
            )

    agent = ResearchAgent(
        provider=EmptyResearchProvider()
    )

    context = ExecutionContext(
        user_id="demo-user",
        request="A very specific research question",
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert isinstance(
        result.output,
        IntelligenceContext,
    )

    assert result.output.source_count == 0

    assert result.output.has_sources is False
