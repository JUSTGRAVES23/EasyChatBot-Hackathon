from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    NOT_CONFIGURED = "not_configured"


@dataclass(frozen=True)
class HealthCheckResult:
    """Sanitized result of one dependency health check."""

    name: str
    status: HealthStatus
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status is HealthStatus.HEALTHY


@dataclass(frozen=True)
class ProductionReadinessResult:
    """Aggregated, dashboard-safe production readiness result."""

    status: HealthStatus
    checks: tuple[HealthCheckResult, ...]

    @property
    def ready(self) -> bool:
        return self.status is HealthStatus.HEALTHY

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "ready": self.ready,
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "details": dict(check.details),
                }
                for check in self.checks
            },
        }
