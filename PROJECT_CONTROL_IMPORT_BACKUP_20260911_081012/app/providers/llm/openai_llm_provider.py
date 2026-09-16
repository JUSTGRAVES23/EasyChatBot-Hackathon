"""OpenAI adapter for the live application provider path."""

from __future__ import annotations

import os
import time

from openai import AsyncOpenAI

from app.providers.llm.llm_provider import LLMProvider
from app.providers.provider_result import ProviderResult, ProviderUsage


class OpenAILLMProvider(LLMProvider):
    """Infrastructure adapter that normalizes OpenAI responses."""

    def __init__(
        self,
        *,
        model: str | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.model = (
            model
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        ).strip()

        if not self.model:
            raise ValueError("OpenAI model cannot be empty.")

        if client is not None:
            self.client = client
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")

        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
    ) -> ProviderResult:
        started = time.perf_counter()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
        except Exception as exc:
            return ProviderResult(
                success=False,
                provider_id="openai",
                model=self.model,
                latency_ms=(time.perf_counter() - started) * 1000,
                error=str(exc),
            )

        content = (
            response.choices[0].message.content
            if response.choices
            else None
        ) or ""

        if not content.strip():
            return ProviderResult(
                success=False,
                provider_id="openai",
                model=self.model,
                provider_request_id=getattr(response, "id", None),
                latency_ms=(time.perf_counter() - started) * 1000,
                error="OpenAI returned an empty response.",
            )

        native_usage = getattr(response, "usage", None)

        usage = ProviderUsage(
            input_tokens=getattr(native_usage, "prompt_tokens", None),
            output_tokens=getattr(native_usage, "completion_tokens", None),
            total_tokens=getattr(native_usage, "total_tokens", None),
        )

        return ProviderResult(
            success=True,
            provider_id="openai",
            model=self.model,
            content=content,
            usage=usage,
            provider_request_id=getattr(response, "id", None),
            latency_ms=(time.perf_counter() - started) * 1000,
            metadata={
                "finish_reason": (
                    getattr(response.choices[0], "finish_reason", None)
                    if response.choices
                    else None
                )
            },
        )

