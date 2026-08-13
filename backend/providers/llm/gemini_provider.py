"""
Gemini LLM Provider.

Concrete Gemini implementation of the provider-independent
LLMProvider contract used by the EasyChatBot hackathon runtime.

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
      GeminiProvider
            |
            v
       Gemini API
            |
            v
      ProviderResult

Responsibilities:
- execute ConversationRequest through Gemini
- use the configured Gemini model
- translate Gemini responses into ProviderResult
- isolate the Gemini SDK from the application/runtime layers

Does not:
- build application workflows
- perform research
- manage memory
- select providers
- manage conversations
- modify application state

The provider uses Google's current `google-genai` SDK.
The SDK client is injectable so unit tests do not need a real
Gemini API call.
"""

from __future__ import annotations

import logging
import os
from typing import Any

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


class GeminiProvider(LLMProvider):
    """
    Gemini implementation of the LLMProvider contract.

    The Google Gemini SDK is deliberately isolated inside this
    infrastructure adapter.

    Args:
        model:
            Gemini model identifier.

        client:
            Optional injected `google.genai.Client`.

            Dependency injection allows unit tests to provide a
            fake client without making a real API call.
    """

    def __init__(
        self,
        model: str = "gemini-3.6-flash",
        client: Any | None = None,
    ) -> None:
        super().__init__(
            provider_id="gemini",
        )

        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                "Gemini model cannot be empty."
            )

        self.model = model.strip()
        self._client = client

    def _get_client(self) -> Any:
        """
        Lazily create the Google GenAI client.

        The API key is read from GEMINI_API_KEY and is never
        hard-coded into the provider.
        """

        if self._client is not None:
            return self._client

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is required."
            )

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "The google-genai package is required for "
                "GeminiProvider. Install it with: "
                "pip install google-genai"
            ) from exc

        self._client = genai.Client(
            api_key=api_key,
        )

        return self._client

    @staticmethod
    def _build_contents(
        request: ConversationRequest,
    ) -> str:
        """
        Convert the provider-independent request into the
        user-facing content sent to Gemini.

        System behaviour remains separate and is supplied through
        Gemini's system_instruction configuration.

        Live intelligence, when present, is deliberately carried
        through the existing ConversationRequest context rather
        than retrieved by Gemini itself.
        """

        sections: list[str] = []

        if request.conversation_context:
            sections.extend(
                (
                    "CONTEXT:",
                    request.conversation_context.strip(),
                    "",
                )
            )

        sections.extend(
            (
                "USER REQUEST:",
                request.user_prompt.strip(),
            )
        )

        return "\n".join(sections)

    async def generate(
        self,
        request: ConversationRequest,
    ) -> ProviderResult:
        """
        Generate a response using Gemini.

        Returns a provider-independent ProviderResult and never
        exposes Gemini SDK response objects to the application.
        """

        if request is None:
            raise ValueError(
                "Conversation request cannot be None."
            )

        try:
            client = self._get_client()

            from google.genai import types

            contents = self._build_contents(
                request,
            )

            config = types.GenerateContentConfig(
                system_instruction=(
                    request.system_instruction
                ),
            )

            response = await client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

        except Exception as exc:
            logger.exception(
                "Gemini provider execution failed."
            )

            return ProviderResult(
                success=False,
                provider_id=self.provider_id,
                output=None,
                error=str(exc),
            )

        output_text = getattr(
            response,
            "text",
            None,
        )

        if not output_text or not output_text.strip():
            return ProviderResult(
                success=False,
                provider_id=self.provider_id,
                output=None,
                error="Gemini returned an empty response.",
            )

        return ProviderResult(
            success=True,
            provider_id=self.provider_id,
            output=output_text.strip(),
        )