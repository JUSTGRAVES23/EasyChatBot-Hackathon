"""
Gemini LLM Provider.

Concrete Gemini implementation of the provider-independent
LLMProvider contract used by the EasyChatBot hackathon runtime.

The provider isolates the Google Gemini SDK from application
and runtime layers.

Structured output is opt-in through ConversationRequest.
"""

from __future__ import annotations

import logging
import os
from typing import Any

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


class GeminiProvider(LLMProvider):
    """
    Gemini implementation of the LLMProvider contract.

    The Google Gemini SDK is deliberately isolated inside this
    infrastructure adapter.
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
        """Lazily create the Google GenAI client."""

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
        """Convert the provider-independent request into Gemini content."""

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

    @staticmethod
    def _build_config(
        request: ConversationRequest,
        types: Any,
    ) -> Any:
        """
        Translate provider-independent request configuration
        into Gemini-specific generation configuration.
        """

        config_kwargs: dict[str, Any] = {
            "system_instruction": request.system_instruction,
        }

        if request.response_schema is not None:
            config_kwargs.update(
                {
                    "response_mime_type": "application/json",
                    "response_schema": request.response_schema,
                }
            )

        return types.GenerateContentConfig(
            **config_kwargs,
        )

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

            config = self._build_config(
                request,
                types,
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

