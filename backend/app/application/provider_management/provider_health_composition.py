"""
EasyChatBot provider health composition.

Builds the provider-health application graph used by the
Operations Center.

Composition only:

    OllamaCloudHealthProbe
            |
            v
    ProviderHealthProbeRunner
            |
            v
    ProviderHealthApplicationService
            |
            +-----------------------------+
            |                             |
            v                             v
    ProviderHealthMonitorService   ProviderIncidentService
            |                             |
            v                             v
    ProviderHealthReadModel        Incident lifecycle

This module does NOT:

- implement provider-specific health logic;
- call provider APIs directly;
- calculate provider health;
- render dashboard data;
- modify Runtime routing;
- perform autonomous failover;
- perform autonomous remediation.

Provider-specific probes are injected into the generic
ProviderHealthProbeRunner.
"""

from __future__ import annotations

import os

from app.application.provider_management.provider_health_application_service import (
    ProviderHealthApplicationService,
)
from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
)
from app.application.provider_management.provider_health_probe_runner import (
    ProviderHealthProbeRunner,
)
from app.application.provider_management.provider_incident_service import (
    InMemoryProviderIncidentRepository,
    ProviderIncidentService,
)
from providers.health.ollama_cloud_health_probe import (
    OllamaCloudHealthProbe,
)


DEFAULT_OLLAMA_CLOUD_MODEL = "gpt-oss:120b"


def create_provider_health_probe_runner(
    *,
    ollama_api_key: str | None = None,
    ollama_model: str | None = None,
    ollama_timeout_seconds: float = 10.0,
    health_monitor: ProviderHealthMonitorService | None = None,
    incident_service: ProviderIncidentService | None = None,
) -> ProviderHealthProbeRunner:
    """
    Build the provider-health runner for the Operations Center.

    Configuration is supplied explicitly where possible.
    Environment variables are used only at this composition
    boundary for the provider credential and model selection.

    The provider API key never leaves this backend composition
    boundary and is never exposed to the frontend.
    """

    api_key = (
        ollama_api_key
        if ollama_api_key is not None
        else os.getenv("OLLAMA_API_KEY", "")
    )

    model = (
        ollama_model
        if ollama_model is not None
        else os.getenv(
            "OLLAMA_CLOUD_MODEL",
            DEFAULT_OLLAMA_CLOUD_MODEL,
        )
    )

    if not api_key.strip():
        raise ValueError(
            "OLLAMA_API_KEY is required to configure "
            "the Ollama Cloud provider health probe."
        )

    if not model.strip():
        raise ValueError(
            "Ollama Cloud model cannot be empty."
        )

    if ollama_timeout_seconds <= 0:
        raise ValueError(
            "Ollama Cloud timeout must be positive."
        )

    monitor = (
        health_monitor
        if health_monitor is not None
        else ProviderHealthMonitorService()
    )

    incidents = (
        incident_service
        if incident_service is not None
        else ProviderIncidentService(
            repository=InMemoryProviderIncidentRepository(),
        )
    )

    application_service = ProviderHealthApplicationService(
        health_monitor=monitor,
        incident_service=incidents,
    )

    ollama_probe = OllamaCloudHealthProbe(
        api_key=api_key,
        model=model,
        timeout_seconds=ollama_timeout_seconds,
    )

    return ProviderHealthProbeRunner(
        health_application_service=application_service,
        probes=(ollama_probe,),
    )


__all__ = [
    "DEFAULT_OLLAMA_CLOUD_MODEL",
    "create_provider_health_probe_runner",
]
