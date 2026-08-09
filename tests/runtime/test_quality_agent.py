import pytest

from backend.agents.quality_agent import (
    QualityAgent,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


@pytest.mark.asyncio
async def test_quality_agent():

    agent = QualityAgent()

    context = ExecutionContext(
        user_id="system",
        request=(
            "Evaluate AI response quality"
        ),
    )

    result = await agent.execute(
        context
    )

    assert result.success is True

    assert result.agent_id == (
        "quality_agent"
    )

    assert result.output["passed"] is True