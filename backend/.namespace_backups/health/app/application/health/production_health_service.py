from __future__ import annotations

from app.application.health.production_readiness_service import (
    ProductionReadinessService,
)
from app.application.health.production_health_configuration import (
    ProductionHealthConfiguration,
)
from app.application.health.health_result import (
    ProductionReadinessResult,
)


class ProductionHealthService:
    """
    Application service exposing production health status.

    Responsibilities:

    - Compose approved production health checks.
    - Execute readiness validation.
    - Return sanitized structured results.

    Does NOT:

    - Render dashboards.
    - Store monitoring data.
    - Send notifications.
    - Access Telegram conversations.
    """

    def __init__(
        self,
        *,
        configuration: ProductionHealthConfiguration,
    ) -> None:

        if configuration is None:
            raise ValueError(
                "configuration cannot be None."
            )

        self._readiness_service = (
            ProductionReadinessService(
                checks=(
                    configuration.build_checks()
                )
            )
        )

    async def check_production_health(
        self,
    ) -> ProductionReadinessResult:
        """
        Execute production dependency checks.
        """

        return await (
            self._readiness_service
            .check()
        )


__all__ = [
    "ProductionHealthService",
]

