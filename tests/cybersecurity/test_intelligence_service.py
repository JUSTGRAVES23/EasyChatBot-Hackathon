import pytest

from cybersecurity.demo_data_source import (
    DemoCybersecurityDataSource,
)
from cybersecurity.intelligence_service import (
    CybersecurityIntelligenceService,
)


@pytest.mark.asyncio
async def test_demo_data_flows_through_intelligence_agent():
    service = CybersecurityIntelligenceService(
        data_source=DemoCybersecurityDataSource(),
    )

    result = await service.analyse(
        user_id="demo-user",
        request="Assess the current cybersecurity posture.",
    )

    assert result.success is True
    assert result.agent_id == "cybersecurity.intelligence"
    assert result.output["signal_count"] == 5
    assert result.output["critical_count"] == 1
    assert result.output["high_count"] == 2
    assert result.output["posture"] == "CRITICAL ATTENTION REQUIRED"
    assert result.output["priority_signals"][0]["severity"] == "critical"

