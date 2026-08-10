"""
Research Service.

Coordinates the Research Agent and exposes a
provider-independent intelligence capability.

Architecture:

Application / Runtime
        |
        v
ResearchService
        |
        v
ResearchAgent
        |
        v
Search Provider
        |
        v
IntelligenceContext

The service does not know about Parallel SDK details.
"""

from __future__ import annotations

from backend.agents.research_agent import (
    ResearchAgent,
)

from backend.intelligence.intelligence_context import (
    IntelligenceContext,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


class ResearchService:
    """
    Application-facing service for live research.

    The service coordinates the Research Agent but does
    not implement provider-specific search behaviour.
    """

    def __init__(
        self,
        agent: ResearchAgent | None = None,
    ) -> None:
        self.agent = (
            agent
            or ResearchAgent()
        )

    async def research(
        self,
        user_id: str,
        query: str,
    ) -> IntelligenceContext:
        """
        Execute research and return normalized intelligence.

        Args:
            user_id:
                Identifier for the current user/session.

            query:
                Research question.

        Returns:
            Provider-independent IntelligenceContext.

        Raises:
            ValueError:
                If the query is empty.

            RuntimeError:
                If the Research Agent fails.
        """

        if not query.strip():
            raise ValueError(
                "Research query cannot be empty."
            )

        context = ExecutionContext(
            user_id=user_id,
            request=query,
        )

        result = await self.agent.execute(
            context
        )

        if not result.success:
            raise RuntimeError(
                result.error
                or "Research execution failed."
            )

        if not isinstance(
            result.output,
            IntelligenceContext,
        ):
            raise TypeError(
                "Research Agent did not return "
                "an IntelligenceContext."
            )

        return result.output