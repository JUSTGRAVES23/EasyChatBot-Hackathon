import pytest

from agents.agent_result import (
    AgentResult,
)

from intelligence.intelligence_context import (
    IntelligenceContext,
)

from intelligence.research_service import (
    ResearchService,
)


class FakeResearchAgent:

    async def execute(
        self,
        context,
    ):
        return AgentResult(
            success=True,
            agent_id="research_agent",
            output=IntelligenceContext(
                query=context.request,
            ),
        )


class FailingResearchAgent:

    async def execute(
        self,
        context,
    ):
        return AgentResult(
            success=False,
            agent_id="research_agent",
            output=None,
            error="Research unavailable",
        )


@pytest.mark.asyncio
async def test_research_service_returns_intelligence_context():

    service = ResearchService(
        agent=FakeResearchAgent()
    )

    result = await service.research(
        user_id="demo-user",
        query="Latest European AI regulation",
    )

    assert isinstance(
        result,
        IntelligenceContext,
    )

    assert result.query == (
        "Latest European AI regulation"
    )


@pytest.mark.asyncio
async def test_research_service_rejects_empty_query():

    service = ResearchService(
        agent=FakeResearchAgent()
    )

    with pytest.raises(
        ValueError,
        match="Research query cannot be empty",
    ):
        await service.research(
            user_id="demo-user",
            query="",
        )


@pytest.mark.asyncio
async def test_research_service_propagates_failure():

    service = ResearchService(
        agent=FailingResearchAgent()
    )

    with pytest.raises(
        RuntimeError,
        match="Research unavailable",
    ):
        await service.research(
            user_id="demo-user",
            query="Latest European AI regulation",
        )
