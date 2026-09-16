from __future__ import annotations

import logging
from typing import Iterable

from .dependency_checks import HealthDependencyCheck
from .health_result import (
    HealthCheckResult,
    HealthStatus,
    ProductionReadinessResult,
)

logger = logging.getLogger(__name__)


class ProductionReadinessService:
    """Runs independent production dependency checks.

    A failed probe is converted into a sanitized unhealthy result and does
    not prevent the remaining probes from running.
    """

    def __init__(
        self,
        *,
        checks: Iterable[HealthDependencyCheck],
    ) -> None:
        resolved = tuple(checks)
        names = [check.name for check in resolved]

        if len(names) != len(set(names)):
            raise ValueError("Health check names must be unique.")

        self._checks = resolved

    async def check(self) -> ProductionReadinessResult:
        results: list[HealthCheckResult] = []

        for dependency in self._checks:
            try:
                result = await dependency.check()
            except Exception:
                logger.exception(
                    "Production dependency health check failed: %s",
                    dependency.name,
                )
                result = HealthCheckResult(
                    name=dependency.name,
                    status=HealthStatus.UNHEALTHY,
                    details={"reason": "health_check_failed"},
                )

            results.append(result)

        ready = bool(results) and all(
            result.status is HealthStatus.HEALTHY
            for result in results
        )

        return ProductionReadinessResult(
            status=(
                HealthStatus.HEALTHY
                if ready
                else HealthStatus.UNHEALTHY
            ),
            checks=tuple(results),
        )
