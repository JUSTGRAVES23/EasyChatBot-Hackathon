"""
EasyChatBot Runtime Engine.

The Runtime is responsible for orchestrating
agent execution.

Responsibilities:
- receive execution requests
- provide execution context
- call approved agents
- return structured results

The Runtime does not:
- implement business logic
- call providers directly
- manage user interfaces
"""

from backend.agents.base_agent import BaseAgent
from backend.agents.agent_result import AgentResult
from backend.runtime.context.execution_context import ExecutionContext


class RuntimeEngine:
    """
    Central execution orchestrator.

    Agents execute through the Runtime.
    """

    async def execute(
        self,
        agent: BaseAgent,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Execute an agent using runtime control.

        Args:
            agent:
                Agent implementation.

            context:
                Runtime execution context.

        Returns:
            AgentResult.
        """

        return await agent.execute(context)