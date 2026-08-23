"""
EasyChatBot AI Operations Center provider health probe contract.

Defines the application-facing contract for provider health
observations.

Architecture:

Provider-specific Health Probe
        |
        v
ProviderHealthProbe
        |
        v
ProviderHealthObservation
        |
        v
ProviderHealthApplicationService
        |
        v
Operations Center

Responsibilities:

- define the contract implemented by provider health probes;
- expose provider/model/capability identity;
- produce one immutable health observation;
- keep provider-specific implementation details outside
  the application layer.

Does NOT:

- update the dashboard;
- create incidents;
- create escalations;
- modify Runtime routing;
- perform autonomous failover;
- expose provider SDK objects.
"""

from __future__ import annotations

from typing import Protocol

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
)


class ProviderHealthProbe(Protocol):
    """
    Provider-independent health probe contract.

    Concrete implementations belong outside the application
    orchestration layer.

    Examples:

        OpenAIHealthProbe
        GeminiHealthProbe
        ParallelHealthProbe
        OllamaHealthProbe
    """

    @property
    def provider(self) -> str:
        """Return the stable provider identifier."""
        ...

    @property
    def model(self) -> str | None:
        """Return the model being health-checked."""
        ...

    @property
    def capability(self) -> str | None:
        """Return the capability being health-checked."""
        ...

    async def check(self) -> ProviderHealthObservation:
        """
        Execute one provider health observation.

        Implementations must return a provider-independent
        ProviderHealthObservation.

        They must not return provider SDK objects.
        """
        ...