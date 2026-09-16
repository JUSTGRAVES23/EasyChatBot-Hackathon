"""
LLM Service.

Application-level service responsible for executing
provider-independent ConversationRequest objects.

Architecture:

ConversationAgent
|
v
LLMService
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

- receive a ConversationRequest
- delegate execution to an injected LLMProvider
- return the provider-independent ProviderResult
- keep provider execution behind an application service boundary

Does not:

- build prompts
- manage characters
- perform research
- select providers
- create providers
- call provider SDKs directly
- manage memory
- manage conversations
- modify application state
"""

from __future__ import annotations

import logging

from conversation.conversation_request import (
    ConversationRequest,
)

from providers.llm.llm_provider import (
    LLMProvider,
)

from providers.provider_result import (
    ProviderResult,
)


logger = logging.getLogger(__name__)


class LLMService:
    """
    Application service for LLM execution.

    The service depends only on the provider-independent
    LLMProvider contract.

    Provider construction and provider selection remain
    outside this service.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
    ) -> None:
        """
        Initialise the LLM service.

        Parameters
        ----------
        llm_provider:
            Provider implementing the LLMProvider contract.
        """

        if llm_provider is None:
            raise ValueError(
                "LLM provider cannot be None."
            )

        self.llm_provider = llm_provider

    async def generate(
        self,
        request: ConversationRequest,
    ) -> ProviderResult:
        """
        Generate an LLM response.

        The service delegates execution to the injected
        provider without knowing the provider's concrete
        implementation.

        Parameters
        ----------
        request:
            Provider-independent conversation request.

        Returns
        -------
        ProviderResult
            Standard provider execution result.

        Raises
        ------
        ValueError
            If the conversation request is None.

        RuntimeError
            If the provider returns no result.
        """

        if request is None:
            raise ValueError(
                "Conversation request cannot be None."
            )

        logger.info(
            "LLM generation started."
        )

        result = await self.llm_provider.generate(
            request
        )

        if result is None:
            raise RuntimeError(
                "LLM provider returned no result."
            )

        logger.info(
            (
                "LLM generation completed. "
                "success=%s provider=%s"
            ),
            result.success,
            result.provider_id,
        )

        return result
