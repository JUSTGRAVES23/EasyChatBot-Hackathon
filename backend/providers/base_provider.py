"""
Base Provider Contract.

Defines the interface for external AI and knowledge providers.

Examples:
- Gemini
- Parallel Search
- Future LLM providers

The Runtime communicates with providers through this contract.

Providers are replaceable implementations.
The Agent layer must remain independent from provider details.
"""

from abc import ABC, abstractmethod

from backend.providers.provider_result import ProviderResult
from backend.runtime.context.execution_context import ExecutionContext


class BaseProvider(ABC):
    """
    Abstract base class for EasyChatBot providers.

    Providers are responsible for communicating
    with external services.

    They are NOT responsible for:
    - agent decisions
    - workflow orchestration
    - memory management
    - user interaction
    """

    provider_id: str

    def __init__(
        self,
        provider_id: str,
    ):
        """
        Initialise provider.

        Args:
            provider_id:
                Unique provider identifier.
        """

        self.provider_id = provider_id

    @abstractmethod
    async def execute(
        self,
        context: ExecutionContext,
    ) -> ProviderResult:
        """
        Execute provider operation.

        Args:
            context:
                Runtime execution context.

        Returns:
            ProviderResult containing provider output.
        """

        pass