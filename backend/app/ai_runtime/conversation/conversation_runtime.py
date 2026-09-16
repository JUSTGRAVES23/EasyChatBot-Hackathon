from __future__ import annotations

from dataclasses import dataclass

from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.providers.llm.llm_provider import LLMProvider
from app.providers.provider_result import ProviderResult


@dataclass(frozen=True, slots=True)
class ConversationRuntime:
    """Execute conversation requests and optionally capture provider usage."""

    llm_provider: LLMProvider
    usage_capture: ProviderUsageCapture | None = None
    usage_context: ProviderUsageContext | None = None

    async def respond(
        self,
        *,
        character_instruction: str,
        learner_message: str,
    ) -> str:
        result = await self.llm_provider.generate(
            system_prompt=character_instruction,
            user_message=learner_message,
        )

        if isinstance(result, ProviderResult):
            if self.usage_capture is not None:
                if self.usage_context is None:
                    raise RuntimeError(
                        "Provider usage capture requires usage context."
                    )
                self.usage_capture.capture(
                    result=result,
                    context=self.usage_context,
                )

            if not result.success:
                raise RuntimeError(result.error or "Provider request failed.")
            return result.content

        if isinstance(result, str):
            return result

        raise TypeError(
            "LLM provider must return ProviderResult or str, "
            f"got {type(result).__name__}"
        )

