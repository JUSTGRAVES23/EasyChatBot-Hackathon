"""
LLM Provider Contract.

Defines the provider-independent contract for language
model providers used by the EasyChatBot hackathon runtime.

The contract sits between the Conversation Agent and
concrete LLM provider implementations.

Architecture:

ConversationAgent
        |
        v
ConversationRequest
        |
        v
LLMProvider
        |
        v
Concrete LLM Provider
        |
        v
ProviderResult

Responsibilities:

- define the LLM generation boundary
- keep ConversationAgent independent from provider SDKs
- provide a stable contract for concrete LLM providers

Does not:

- call an external API
- contain provider SDK logic
- select models
- implement routing
- manage memory
- manage conversations
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from backend.conversation.conversation_request import (
    ConversationRequest,
)

from backend.providers.provider_result import (
    ProviderResult,
)


class LLMProvider(ABC):
    """
    Abstract provider contract for language model generation.

    Concrete implementations may use OpenAI, Ollama,
    Gemini, or another approved LLM provider.

    The application and agent layers depend only on
    this contract.
    """

    provider_id: str

    def __init__(
        self,
        provider_id: str,
    ) -> None:
        """
        Initialise the LLM provider.

        Args:
            provider_id:
                Stable identifier for the concrete provider.
        """

        if not provider_id.strip():
            raise ValueError(
                "LLM provider_id cannot be empty."
            )

        self.provider_id = provider_id

    @abstractmethod
    async def generate(
        self,
        request: ConversationRequest,
    ) -> ProviderResult:
        """
        Generate an LLM response.

        Args:
            request:
                Provider-independent conversation request.

        Returns:
            ProviderResult containing the generated
            response or an error.

        Implementations must not expose provider SDK
        objects through the result.
        """

        raise NotImplementedError