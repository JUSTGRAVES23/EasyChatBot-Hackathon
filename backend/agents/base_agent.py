"""
Base AI Agent Contract.

All EasyChatBot AI Agents inherit this contract.

The BaseAgent defines:
- agent identity
- execution interface
- runtime interaction

Agents do not:
- call providers directly
- manage memory
- modify external systems

The AI Runtime controls execution.
"""

from abc import ABC, abstractmethod

from runtime.context.execution_context import ExecutionContext
from agents.agent_manifest import AgentManifest
from agents.agent_result import AgentResult


class BaseAgent(ABC):
    """
    Abstract base class for EasyChatBot agents.
    """

    def __init__(
        self,
        manifest: AgentManifest,
    ):
        """
        Initialise an agent.

        Args:
            manifest:
                Agent identity definition.
        """

        self.manifest = manifest

    @abstractmethod
    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Execute the agent.

        Args:
            context:
                Runtime execution context.

        Returns:
            AgentResult.
        """

        pass
