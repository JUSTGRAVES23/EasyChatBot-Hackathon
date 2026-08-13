"""
OpenAI LLM Provider.

Concrete LLM provider implementation for the EasyChatBot
hackathon runtime.

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
OpenAIProvider
|
v
OpenAI Responses API
|
v
ProviderResult

Responsibilities:

- execute ConversationRequest through OpenAI
- use the configured OpenAI model
- translate the OpenAI response into ProviderResult
- isolate the OpenAI SDK from the application layer

Does not:

- build prompts
- manage characters
- manage memory
- perform research
- perform routing
- modify application state
"""

from __future__ import annotations

import logging
import os

from openai import AsyncOpenAI

from backend.conversation.conversation_request import (
    ConversationRequest,
)

from backend.providers.llm.llm_provider import (
    LLMProvider,
)

from backend.providers.provider_result import (
    ProviderResult,
)


logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI implementation of the LLMProvider contract.

    The OpenAI SDK is deliberately isolated inside this
    infrastructure adapter.
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        client: AsyncOpenAI | None = None,
    ) -> None:
        """
        Initialise the OpenAI provider.

        Parameters
        ----------
        model:
            OpenAI model identifier.

        client:
            Optional injected AsyncOpenAI client.

            Dependency injection allows unit tests to
            provide a fake client without making a real
            API call.
        """

        super().__init__(
            provider_id="openai",
        )

        if not isinstance(
            model,
            str,
        ):
            raise ValueError(
                "OpenAI model must be a string."
            )

        model = model.strip()

        if not model:
            raise ValueError(
                "OpenAI model cannot be empty."
            )

        self.model = model

        if client is not None:
            self._client = client
            return

        api_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not configured."
            )

        self._client = AsyncOpenAI(
            api_key=api_key,
        )

    async def generate(
        self,
        request: ConversationRequest,
    ) -> ProviderResult:
        """
        Generate a response using OpenAI.

        The provider translates the provider-independent
        ConversationRequest into the OpenAI Responses API
        request.

        Parameters
        ----------
        request:
            Provider-independent conversation request.

        Returns
        -------
        ProviderResult
            Provider-independent execution result.

        Raises
        ------
        ValueError
            If request is None.
        """

        if request is None:
            raise ValueError(
                "Conversation request cannot be None."
            )

        messages = [
            {
                "role": "system",
                "content": request.system_instruction,
            },
        ]

        if request.conversation_context:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Additional context:\n"
                        f"{request.conversation_context}"
                    ),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": request.user_prompt,
            }
        )

        try:
            response = (
                await self._client.responses.create(
                    model=self.model,
                    input=messages,
                )
            )

        except Exception as exc:
            logger.exception(
                "OpenAI provider execution failed."
            )

            return ProviderResult(
                success=False,
                provider_id=self.provider_id,
                error=str(exc),
            )

        output_text = getattr(
            response,
            "output_text",
            None,
        )

        if not output_text:
            return ProviderResult(
                success=False,
                provider_id=self.provider_id,
                error=(
                    "OpenAI returned an empty response."
                ),
            )

        return ProviderResult(
            success=True,
            provider_id=self.provider_id,
            output=output_text,
        )