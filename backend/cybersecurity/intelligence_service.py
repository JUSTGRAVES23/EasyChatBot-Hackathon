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

This is currently a compatibility path for the existing
Cybersecurity Intelligence integration.

It does NOT:

- call provider SDKs;
- execute remediation;
- send email;
- modify production systems;
- bypass the supplied Runtime boundary.
"""

from __future__ import annotations

from uuid import uuid4

from agents.agent_result import (
    AgentResult,
)

from agents.cybersecurity_intelligence_agent import (
    CybersecurityIntelligenceAgent,
)

from cybersecurity.data_source import (
    CybersecurityDataSource,
)

from runtime.context.execution_context import (
    ExecutionContext,
)

from runtime.runtime_engine import (
    RuntimeEngine,
)


class CybersecurityIntelligenceService:
    """
    Application boundary for Cybersecurity Intelligence.

    The service acquires normalized signals and delegates
    agent execution to the existing RuntimeEngine.

    The legacy RuntimeEngine remains isolated here until a
    dedicated cybersecurity migration to the canonical Runtime
    contract is completed and verified.
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
        Agent 1 through the current Runtime boundary.
        """

        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )

        if not isinstance(request, str) or not request.strip():
            raise ValueError(
                "request cannot be empty."
            )

        signals = (
            await self.data_source.get_signals()
        )

        context = ExecutionContext(
            execution_id=str(uuid4()),
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

