import pytest

from agents.cybersecurity_intelligence_agent import (
    CybersecurityIntelligenceAgent,
)
from cybersecurity.intelligence_models import (
    CybersecuritySignal,
)
from runtime.context.execution_context import ExecutionContext


@pytest.mark.asyncio
async def test_agent_prioritises_critical_signal():
    agent = CybersecurityIntelligenceAgent()

    context = ExecutionContext(
        user_id="test-user",
        request="Assess current cybersecurity posture.",
        metadata={
            "cybersecurity_signals": [
                CybersecuritySignal(
                    signal_id="sig-1",
                    category="vulnerability",
                    title="Critical dependency vulnerability",
                    severity="critical",
                    confidence=0.98,
                    source="security-scanner",
                    affected_area="backend",
                    status="open",
                ),
                CybersecuritySignal(
                    signal_id="sig-2",
                    category="event",
                    title="Low severity event",
                    severity="low",
                    confidence=0.90,
                    source="security-events",
                    status="open",
                ),
            ]
        },
    )

    result = await agent.execute(context)

    assert result.success is True
    assert result.output["posture"] == "CRITICAL ATTENTION REQUIRED"
    assert result.output["critical_count"] == 1
    assert result.output["priority_signals"][0]["signal_id"] == "sig-1"


@pytest.mark.asyncio
async def test_agent_requires_security_signals():
    agent = CybersecurityIntelligenceAgent()

    context = ExecutionContext(
        user_id="test-user",
        request="Assess security.",
    )

    result = await agent.execute(context)

    assert result.success is False
    assert "cybersecurity_signals" in result.error

