"""
LLM Provider Factory.

Responsible only for selecting the configured LLM provider.

Supported providers:
- openai
- ollama

Configuration:

LLM_PROVIDER=openai

or

LLM_PROVIDER=ollama
"""

from __future__ import annotations

import os

from app.providers.llm.llm_provider import (
    LLMProvider,
)

from app.providers.llm.openai_llm_provider import (
    OpenAILLMProvider,
)

from app.providers.llm.ollama_llm_provider import (
    OllamaLLMProvider,
)


class LLMProviderFactory:
    """
    Factory for creating LLM providers.

    Provider selection is configuration driven.
    """

    @staticmethod
    def create() -> LLMProvider:

        provider = os.getenv(
            "LLM_PROVIDER",
            "ollama",
        ).lower()


        if provider == "openai":

            return OpenAILLMProvider()


        if provider == "ollama":

            return OllamaLLMProvider()


        raise ValueError(
            f"Unsupported LLM provider: {provider}"
        )
