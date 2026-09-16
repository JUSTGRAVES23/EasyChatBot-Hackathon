from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.infrastructure.health.llm_provider_health_check import (
    LLMProviderHealthCheck,
)
from app.infrastructure.health.postgresql_health_check import (
    PostgreSQLHealthCheck,
)
from app.infrastructure.health.telegram_health_check import (
    TelegramHealthCheck,
)


@dataclass(frozen=True)
class ProductionHealthConfiguration:
    """
    Composition configuration for production health monitoring.

    Keeps dependency creation outside the readiness service.
    """

    database_engine: Any | None = None

    telegram_bot_factory: Any | None = None

    llm_provider: str | None = None

    llm_request_get: Any | None = None

    def build_checks(self) -> tuple:
        """
        Build production dependency health checks.
        """

        return (
            PostgreSQLHealthCheck(
                engine=self.database_engine,
            ),
            LLMProviderHealthCheck(
                provider=self.llm_provider,
                request_get=self.llm_request_get,
            ),
            TelegramHealthCheck(
                bot_factory=self.telegram_bot_factory,
            ),
        )


__all__ = [
    "ProductionHealthConfiguration",
]


