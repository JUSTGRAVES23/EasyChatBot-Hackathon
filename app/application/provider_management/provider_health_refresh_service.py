"""
EasyChatBot provider health refresh service.

Coordinates one live provider-health refresh cycle.

The service delegates provider execution to the existing
ProviderHealthProbeRunner and does not contain provider-specific
logic or dashboard rendering.
"""

from __future__ import annotations

from app.application.provider_management.provider_health_probe_runner import (
    ProviderHealthProbeResult,
    ProviderHealthProbeRunner,
)


class ProviderHealthRefreshService:
    """
    Application service for one live provider-health refresh.
    """

    def __init__(
        self,
        *,
        probe_runner: ProviderHealthProbeRunner,
    ) -> None:
        if probe_runner is None:
            raise ValueError(
                "Provider health probe runner "
                "cannot be None."
            )

        self._probe_runner = probe_runner

    async def refresh(
        self,
    ) -> tuple[ProviderHealthProbeResult, ...]:
        """
        Execute one refresh cycle across all configured probes.

        Provider execution and observation processing remain
        owned by ProviderHealthProbeRunner.
        """

        return await self._probe_runner.run_all()


__all__ = [
    "ProviderHealthRefreshService",
]
