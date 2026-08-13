"""
LLM Provider Factory.

Creates approved LLM provider implementations.

The factory is the composition boundary between
application/runtime code and infrastructure providers.

Architecture:

Application/API
|
v
LLMProviderFactory
|
v
LLMProvider
|
+--> OpenAIProvider
+--> Future OllamaProvider
+--> GeminiProvider

Responsibilities:

- create configured LLM providers
- isolate provider construction
- provide provider independence
- obtain approved provider configuration

Does not:

- execute LLM requests
- build prompts
- manage conversations
- manage memory
- apply routing decisions
- call provider SDKs directly
"""

from __future__ import annotations

from backend.providers.llm.config import (
    get_gemini_model,
    get_llm_model,
    get_llm_provider_name,
)

from backend.providers.llm.llm_provider import (
    LLMProvider,
)

from backend.providers.llm.openai_provider import (
    OpenAIProvider,
)

from backend.providers.llm.gemini_provider import (
    GeminiProvider,
)


class LLMProviderFactory:
    """
    Factory responsible for creating LLM providers.

    Provider selection and configuration are centralised
    here so application/runtime code does not depend
    directly on concrete infrastructure implementations.
    """

    @staticmethod
    def create(
        provider: str | None = None,
    ) -> LLMProvider:
        """
        Create a configured LLM provider.

        Parameters
        ----------
        provider:
            Optional provider identifier.

            When omitted, the configured provider from
            LLM provider configuration is used.

        Returns
        -------
        LLMProvider
            Configured provider implementation.

        Raises
        ------
        ValueError
            If provider is invalid or unsupported.
        """

        if provider is None:
            provider_name = (
                get_llm_provider_name()
            )
        else:
            if not isinstance(
                provider,
                str,
            ):
                raise ValueError(
                    "Provider name must be a string."
                )

            provider_name = (
                provider.strip().lower()
            )

            if not provider_name:
                raise ValueError(
                    "Provider name cannot be empty."
                )

        if provider_name == "openai":
            return OpenAIProvider(
                model=get_llm_model(),
            )

        if provider_name == "gemini":
            return GeminiProvider(
                model=get_gemini_model(),
            )

        raise ValueError(
            (
                "Unsupported LLM provider: "
                f"{provider_name}"
            )
        )
