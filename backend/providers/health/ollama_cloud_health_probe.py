"""
EasyChatBot Ollama Cloud provider health probe.

Infrastructure adapter for real Ollama Cloud health monitoring.

Architecture:

Ollama Cloud
    |
    v
OllamaCloudHealthProbe
    |
    v
ProviderHealthObservation
    |
    v
Provider Health Application Service
    |
    v
Operations Center

This adapter:

- uses Ollama Cloud;
- never calls localhost:11434;
- performs a minimal real inference request;
- returns the existing provider-independent health model;
- never exposes the API key;
- does not modify Runtime routing;
- does not perform autonomous remediation.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

import httpx

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)


DEFAULT_BASE_URL = "https://ollama.com"
DEFAULT_MODEL = "gpt-oss:120b"
DEFAULT_TIMEOUT_SECONDS = 15.0

HEALTH_CHECK_PROMPT = "Reply with exactly HEALTH_OK"


class OllamaCloudHealthProbe:
    """
    Real Ollama Cloud health probe.

    Configuration:

        OLLAMA_API_KEY
        OLLAMA_CLOUD_BASE_URL
        EASYCHATBOT_OLLAMA_CLOUD_MODEL
        OLLAMA_HEALTH_TIMEOUT_SECONDS
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:

        configured_api_key = (
            api_key
            if api_key is not None
            else os.getenv("OLLAMA_API_KEY")
        )

        configured_base_url = (
            base_url
            if base_url is not None
            else os.getenv(
                "OLLAMA_CLOUD_BASE_URL",
                DEFAULT_BASE_URL,
            )
        )

        configured_model = (
            model
            if model is not None
            else os.getenv(
                "EASYCHATBOT_OLLAMA_CLOUD_MODEL",
                os.getenv(
                    "OLLAMA_CLOUD_MODEL",
                    DEFAULT_MODEL,
                ),
            )
        )

        configured_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(
                os.getenv(
                    "OLLAMA_HEALTH_TIMEOUT_SECONDS",
                    str(DEFAULT_TIMEOUT_SECONDS),
                )
            )
        )

        if (
            not isinstance(configured_api_key, str)
            or not configured_api_key.strip()
        ):
            raise ValueError(
                "OLLAMA_API_KEY is required."
            )

        if not isinstance(configured_base_url, str):
            raise ValueError(
                "Ollama Cloud base URL must be a string."
            )

        if not configured_base_url.strip():
            raise ValueError(
                "Ollama Cloud base URL cannot be empty."
            )

        if not isinstance(configured_model, str):
            raise ValueError(
                "Ollama Cloud model must be a string."
            )

        if not configured_model.strip():
            raise ValueError(
                "Ollama Cloud model cannot be empty."
            )

        if configured_timeout <= 0:
            raise ValueError(
                "Ollama Cloud health timeout must be positive."
            )

        self._api_key = configured_api_key.strip()
        self._base_url = configured_base_url.rstrip("/")
        self._model = configured_model.strip()
        self._timeout_seconds = float(configured_timeout)

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def capability(self) -> str | None:
        return "cloud_llm"

    async def check(
        self,
    ) -> ProviderHealthObservation:

        started = perf_counter()

        try:
            payload = await asyncio.to_thread(
                self._request_chat
            )

            latency_ms = int(
                round(
                    (perf_counter() - started)
                    * 1000
                )
            )

            self._validate_response(payload)

            return self._build_observation(
                status=ProviderHealthStatus.HEALTHY,
                latency_ms=latency_ms,
            )

        except Exception as exc:

            latency_ms = int(
                round(
                    (perf_counter() - started)
                    * 1000
                )
            )

            return self._build_observation(
                status=ProviderHealthStatus.UNAVAILABLE,
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def _request_chat(self) -> dict[str, Any]:

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": HEALTH_CHECK_PROMPT,
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": (
                f"Bearer {self._api_key}"
            ),
        }

        response = httpx.post(
            f"{self._base_url}/api/chat",
            headers=headers,
            json=payload,
            timeout=self._timeout_seconds,
        )

        response.raise_for_status()

        result = response.json()

        if not isinstance(result, dict):
            raise ValueError(
                "Invalid Ollama Cloud response."
            )

        return result

    @staticmethod
    def _validate_response(
        payload: dict[str, Any],
    ) -> None:

        if payload.get("done") is False:
            raise ValueError(
                "Ollama Cloud response did not complete."
            )

        message = payload.get("message")

        if not isinstance(message, dict):
            raise ValueError(
                "Ollama Cloud response contains no message."
            )

        content = message.get("content")

        if (
            not isinstance(content, str)
            or not content.strip()
        ):
            raise ValueError(
                "Ollama Cloud returned empty content."
            )

    def _build_observation(
        self,
        *,
        status: ProviderHealthStatus,
        latency_ms: int,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> ProviderHealthObservation:

        healthy = (
            status
            == ProviderHealthStatus.HEALTHY
        )

        return ProviderHealthObservation(
            provider=self.provider,
            model=self.model,
            capability=self.capability,
            status=status,
            observed_at=datetime.now(
                timezone.utc
            ),
            latency_ms=max(latency_ms, 0),
            error_type=error_type,
            error_message=error_message,
            consecutive_failures=(
                0 if healthy else 1
            ),
            consecutive_successes=(
                1 if healthy else 0
            ),
        )