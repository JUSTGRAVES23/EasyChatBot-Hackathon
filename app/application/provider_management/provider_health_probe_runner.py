"""
EasyChatBot AI Operations Center provider health probe runner.

Coordinates provider-independent health probes with the
existing ProviderHealthApplicationService.

Architecture:

ProviderHealthProbe
        |
        v
ProviderHealthProbeRunner
        |
        v
ProviderHealthApplicationService
        |
        v
ProviderHealthMonitorService
        |
        v
Operations Center

The runner is orchestration only.

It does NOT:

- implement provider-specific API calls;
- calculate health state;
- create incidents directly;
- modify Runtime routing;
- select alternative providers;
- perform autonomous remediation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter
from typing import Iterable

from app.application.provider_management.provider_health_application_service import (
    ProviderHealthApplicationResult,
    ProviderHealthApplicationService,
)
from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)
from app.application.provider_management.provider_health_probe import (
    ProviderHealthProbe,
)


@dataclass(frozen=True)
class ProviderHealthProbeResult:
    """
    Result of processing one provider health probe.

    Contains both the raw provider-independent observation
    and the application result produced by the existing
    health application boundary.
    """

    observation: ProviderHealthObservation

    application_result: ProviderHealthApplicationResult


class ProviderHealthProbeRunner:
    """
    Coordinates provider health probes.

    The runner receives probes through dependency injection.
    It never constructs provider-specific clients itself.
    """

    def __init__(
        self,
        *,
        health_application_service: (
            ProviderHealthApplicationService
        ),
        probes: Iterable[ProviderHealthProbe],
    ) -> None:
        """
        Initialise the probe runner.
        """

        if health_application_service is None:
            raise ValueError(
                "Provider health application service "
                "cannot be None."
            )

        if probes is None:
            raise ValueError(
                "Provider health probes cannot be None."
            )

        self._health_application_service = (
            health_application_service
        )

        self._probes = tuple(probes)

        self._validate_probes()

    async def run_probe(
        self,
        probe: ProviderHealthProbe,
    ) -> ProviderHealthProbeResult:
        """
        Execute one health probe and submit its observation
        through the existing application boundary.
        """

        if probe is None:
            raise ValueError(
                "Provider health probe cannot be None."
            )

        started = perf_counter()

        try:
            observation = await probe.check()

        except Exception as exc:
            elapsed_ms = int(
                round(
                    (perf_counter() - started)
                    * 1000
                )
            )

            observation = (
                self._build_failure_observation(
                    probe=probe,
                    latency_ms=elapsed_ms,
                    error=exc,
                )
            )

        if observation.provider != probe.provider:
            raise ValueError(
                "Provider health probe returned an "
                "observation for a different provider."
            )

        result = (
            self._health_application_service.observe(
                observation
            )
        )

        return ProviderHealthProbeResult(
            observation=observation,
            application_result=result,
        )

    async def run_all(
        self,
    ) -> tuple[ProviderHealthProbeResult, ...]:
        """
        Execute all configured probes.

        Probes are executed sequentially for deterministic
        application behaviour and predictable provider load.

        Parallel execution can be introduced later only if
        measurement demonstrates that it is required.
        """

        results: list[
            ProviderHealthProbeResult
        ] = []

        for probe in self._probes:
            results.append(
                await self.run_probe(probe)
            )

        return tuple(results)

    def _validate_probes(self) -> None:
        """
        Validate configured probe identities.
        """

        providers: set[str] = set()

        for probe in self._probes:
            if probe is None:
                raise ValueError(
                    "Provider health probes cannot contain None."
                )

            provider = probe.provider.strip()

            if not provider:
                raise ValueError(
                    "Provider health probe provider "
                    "cannot be empty."
                )

            if provider in providers:
                raise ValueError(
                    "Duplicate provider health probe "
                    f"configured: {provider}."
                )

            providers.add(provider)

    @staticmethod
    def _build_failure_observation(
        *,
        probe: ProviderHealthProbe,
        latency_ms: int,
        error: Exception,
    ) -> ProviderHealthObservation:
        """
        Convert a probe exception into a provider-independent
        unavailable observation.

        Provider-specific exceptions do not cross the
        application boundary.
        """

        now = datetime.now(
            timezone.utc
        )

        return ProviderHealthObservation(
            provider=probe.provider,
            model=probe.model,
            capability=probe.capability,
            status=ProviderHealthStatus.UNAVAILABLE,
            observed_at=now,
            latency_ms=max(
                latency_ms,
                0,
            ),
            error_type=type(error).__name__,
            error_message=str(error),
            consecutive_failures=1,
            consecutive_successes=0,
        )