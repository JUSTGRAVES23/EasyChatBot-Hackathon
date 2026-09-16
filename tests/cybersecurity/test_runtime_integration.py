import pytest

from cybersecurity.demo_data_source import (
    DemoCybersecurityDataSource,
)
from cybersecurity.intelligence_service import (
    CybersecurityIntelligenceService,
)
from runtime.runtime_engine import RuntimeEngine


@pytest.mark.asyncio
async def test_cybersecurity_intelligence_uses_runtime_boundary():
    service = CybersecurityIntelligenceService(
        data_source=DemoCybersecurityDataSource(),
        runtime=RuntimeEngine(),
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

