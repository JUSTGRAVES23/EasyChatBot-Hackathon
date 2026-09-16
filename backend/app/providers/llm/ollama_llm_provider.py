"""Ollama adapter for the live application provider path."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

from app.providers.llm.llm_provider import LLMProvider
from app.providers.provider_result import ProviderResult, ProviderUsage


logger = logging.getLogger(__name__)


class OllamaLLMProvider(LLMProvider):
    """Infrastructure adapter that normalizes Ollama responses."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.model = (
            model
            or os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        ).strip()

        if not self.model:
            raise ValueError("Ollama model cannot be empty.")

    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        **kwargs: Any,
    ) -> ProviderResult:
        if not user_message:
            raise ValueError("User message cannot be empty.")

        started = time.perf_counter()

        payload = {
            "model": self.model,
            "prompt": (
                f"System:\n{system_prompt}\n\n"
                f"User:\n{user_message}\n\n"
                "Assistant:\n"
            ),
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            logger.exception("Ollama request failed.")
            return ProviderResult(
                success=False,
                provider_id="ollama",
                model=self.model,
                latency_ms=(time.perf_counter() - started) * 1000,
                error="Ollama provider unavailable.",
            )
        except ValueError as exc:
            return ProviderResult(
                success=False,
                provider_id="ollama",
                model=self.model,
                latency_ms=(time.perf_counter() - started) * 1000,
                error=f"Invalid Ollama response: {exc}",
            )

        result = str(data.get("response") or "").strip()

        if not result:
            return ProviderResult(
                success=False,
                provider_id="ollama",
                model=self.model,
                latency_ms=(time.perf_counter() - started) * 1000,
                error="Ollama returned empty response.",
            )

        # Ollama exposes these counters for /api/generate when available.
        usage = ProviderUsage(
            input_tokens=_non_negative_int(data.get("prompt_eval_count")),
            output_tokens=_non_negative_int(data.get("eval_count")),
            total_tokens=_sum_if_available(
                data.get("prompt_eval_count"),
                data.get("eval_count"),
            ),
        )

        return ProviderResult(
            success=True,
            provider_id="ollama",
            model=self.model,
            content=result,
            usage=usage,
            provider_request_id=None,
            latency_ms=(time.perf_counter() - started) * 1000,
            metadata={
                "done": data.get("done"),
                "load_duration_ns": data.get("load_duration"),
                "prompt_eval_duration_ns": data.get("prompt_eval_duration"),
                "eval_duration_ns": data.get("eval_duration"),
            },
        )


def _non_negative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _sum_if_available(left: Any, right: Any) -> int | None:
    left_value = _non_negative_int(left)
    right_value = _non_negative_int(right)
    if left_value is None or right_value is None:
        return None
    return left_value + right_value

