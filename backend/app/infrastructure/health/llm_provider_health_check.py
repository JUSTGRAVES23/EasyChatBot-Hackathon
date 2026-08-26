from __future__ import annotations

import asyncio
import os
from typing import Any

from backend.app.application.health.health_result import (
    HealthCheckResult,
    HealthStatus,
)


class LLMProviderHealthCheck:
    """Read-only health probe for the configured LLM provider.

    Ollama uses /api/tags.

    OpenAI uses the models endpoint.

    Neither probe generates a learner response or sends
    learner content to the provider.
    """

    name = "llm_provider"

    def __init__(
        self,
        *,
        provider: str | None = None,
        request_get: Any | None = None,
        openai_client_factory: Any | None = None,
    ) -> None:
        self._provider = (
            provider
            or os.getenv(
                "LLM_PROVIDER",
                "ollama",
            )
        ).strip().lower()

        self._request_get = request_get
        self._openai_client_factory = (
            openai_client_factory
        )

    async def check(self) -> HealthCheckResult:
        if self._provider == "ollama":
            return await self._check_ollama()

        if self._provider == "openai":
            return await self._check_openai()

        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.UNHEALTHY,
            details={
                "reason": "unsupported_provider",
            },
        )

    async def _check_ollama(
        self,
    ) -> HealthCheckResult:
        base_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        ).rstrip("/")

        try:
            if self._request_get is not None:
                response = await self._request_get(
                    f"{base_url}/api/tags"
                )

                status_code = getattr(
                    response,
                    "status_code",
                    200,
                )

                if status_code >= 400:
                    raise RuntimeError(
                        "Ollama health request failed."
                    )

            else:
                import requests

                response = await asyncio.to_thread(
                    requests.get,
                    f"{base_url}/api/tags",
                    timeout=10,
                )

                response.raise_for_status()

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                details={
                    "provider": "ollama",
                    "reachable": True,
                },
            )

        except Exception:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                details={
                    "provider": "ollama",
                    "reason": "provider_unavailable",
                },
            )

    async def _check_openai(
        self,
    ) -> HealthCheckResult:
        if not os.getenv(
            "OPENAI_API_KEY"
        ):
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.NOT_CONFIGURED,
                details={
                    "provider": "openai",
                    "configured": False,
                },
            )

        try:
            if self._openai_client_factory is None:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(
                    api_key=os.environ[
                        "OPENAI_API_KEY"
                    ],
                )

            else:
                client = (
                    self._openai_client_factory()
                )

            await client.models.list()

            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                details={
                    "provider": "openai",
                    "reachable": True,
                },
            )

        except Exception:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                details={
                    "provider": "openai",
                    "reason": "provider_unavailable",
                },
            )


__all__ = [
    "LLMProviderHealthCheck",
]


