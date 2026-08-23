"""
Cybersecurity Intelligence Application Service.

Application-layer composition for the Cybersecurity
Intelligence Agent.

Flow:

CybersecurityDataSource
        ↓
ExecutionContext
        ↓
RuntimeEngine
        ↓
CybersecurityIntelligenceAgent
        ↓
AgentResult

Does NOT:
- call provider SDKs;
- execute remediation;
- send email;
- modify production systems;
- bypass the Runtime.
"""

from __future__ import annotations

from backend.agents.agent_result import (
    AgentResult,
)

from backend.agents.cybersecurity_intelligence_agent import (
    CybersecurityIntelligenceAgent,
)

from backend.cybersecurity.data_source import (
    CybersecurityDataSource,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from backend.runtime.runtime_engine import (
    RuntimeEngine,
)


class CybersecurityIntelligenceService:
    """
    Application boundary for Cybersecurity Intelligence.

    The service acquires normalized signals and delegates
    agent execution to the existing RuntimeEngine.
    """

    def __init__(
        self,
        data_source: CybersecurityDataSource,
        runtime: RuntimeEngine | None = None,
        agent: CybersecurityIntelligenceAgent | None = None,
    ) -> None:

        if data_source is None:
            raise ValueError(
                "Cybersecurity data source cannot be None."
            )

        self.data_source = data_source

        self.runtime = (
            runtime
            or RuntimeEngine()
        )

        self.agent = (
            agent
            or CybersecurityIntelligenceAgent()
        )

    async def analyse(
        self,
        *,
        user_id: str,
        request: str,
    ) -> AgentResult:
        """
        Acquire cybersecurity signals and execute
        Agent 1 through Runtime.
        """

        if not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )

        if not request.strip():
            raise ValueError(
                "request cannot be empty."
            )

        signals = (
            await self.data_source.get_signals()
        )

        context = ExecutionContext(
            user_id=user_id,
            request=request,
            metadata={
                "cybersecurity_signals": signals,
                "data_source": (
                    self.data_source.source_id
                ),
                "data_mode": "DEMO",
            },
        )

        return await self.runtime.execute(
            agent=self.agent,
            context=context,
        )