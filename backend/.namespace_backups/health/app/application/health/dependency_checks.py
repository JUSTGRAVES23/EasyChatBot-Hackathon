from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


from .health_result import (
    HealthCheckResult,
    HealthStatus,
)


Probe = Callable[[], Awaitable[bool | HealthCheckResult]]


class AsyncDependencyCheck:
    """
    Asynchronous production dependency health check.

    The probe is deliberately isolated from the readiness service.

    A probe may return:

        True
            Dependency is healthy.

        False
            Dependency is unhealthy.

        HealthCheckResult
            Caller-provided sanitized health result.

    Exceptions are contained and converted into a generic
    dependency failure result. Internal exception details,
    credentials, connection strings, and secrets are never
    exposed through the result.
    """

    def __init__(
        self,
        *,
        name: str,
        probe: Probe,
    ) -> None:
        if not name or not name.strip():
            raise ValueError(
                "Dependency check name cannot be empty."
            )

        if not callable(probe):
            raise TypeError(
                "Dependency check probe must be callable."
            )

        self.name = name.strip()
        self.probe = probe

    async def check(self) -> HealthCheckResult:
        """
        Execute the dependency probe safely.
        """

        try:
            result = await self.probe()

        except Exception:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                details={
                    "reason": "dependency_check_failed",
                },
            )

        if isinstance(
            result,
            HealthCheckResult,
        ):
            # Ensure the dependency name remains authoritative.
            if result.name != self.name:
                return HealthCheckResult(
                    name=self.name,
                    status=result.status,
                    details=dict(result.details),
                )

            return result

        if result is True:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
            )

        if result is False:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                details={
                    "reason": "dependency_unhealthy",
                },
            )

        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.UNHEALTHY,
            details={
                "reason": "invalid_probe_result",
            },
        )


class ConfigurationCheck:
    """
    Synchronous configuration/readiness check.

    This check verifies whether a required dependency configuration
    exists without exposing the configuration value itself.
    """

    def __init__(
        self,
        *,
        name: str,
        configured: bool,
    ) -> None:
        if not name or not name.strip():
            raise ValueError(
                "Configuration check name cannot be empty."
            )

        if not isinstance(
            configured,
            bool,
        ):
            raise TypeError(
                "configured must be a boolean."
            )

        self.name = name.strip()
        self.configured = configured

    async def check(self) -> HealthCheckResult:
        """
        Return a sanitized configuration health result.
        """

        if self.configured:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                details={
                    "configured": True,
                },
            )

        return HealthCheckResult(
            name=self.name,
            status=HealthStatus.NOT_CONFIGURED,
            details={
                "configured": False,
            },
        )


# Compatibility contract used by WS-21.6 / WS-21.7.
#
# Keep this alias rather than creating another independent abstraction.
HealthDependencyCheck = AsyncDependencyCheck


__all__ = [
    "AsyncDependencyCheck",
    "ConfigurationCheck",
    "HealthDependencyCheck",
]