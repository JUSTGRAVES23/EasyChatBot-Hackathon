"""Provider-independent LLM contract for the live application runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.providers.provider_result import ProviderResult


class LLMProvider(ABC):
    """Stable boundary between ConversationRuntime and provider adapters."""

    @abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> ProviderResult:
        """Execute an LLM request and return canonical provider metadata."""
        raise NotImplementedError

