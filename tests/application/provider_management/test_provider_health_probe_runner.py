"""
Tests for the EasyChatBot provider health probe runner.

The tests use fake probes and never call external providers.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.provider_health_application_service import (
    ProviderHealthApplicationService,
)

from app.application.provider_management.provider_health_probe_runner import (
    ProviderHealthProbeRunner,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthObservation,
    ProviderHealthStatus,
)

from app.application.provider_management.provider_health_monitor_service import (
    ProviderHealthMonitorService,
)

from app.application.provider_management.provider_incident_service import (
    InMemoryProviderIncidentRepository,
    ProviderIncidentService,
)

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
)


class FakeProbe:
    """
    Deterministic provider health probe.
    """

    def __init__(
        self,
        *,
        provider: str = "openai",
        model: str = "gpt-5-mini",
        capability: str = "conversation",
        status: ProviderHealthStatus = (
            ProviderHealthStatus.HEALTHY
        ),
        error: Exception | None = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._capability = capability
        self._status = status
        self._error = error

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def capability(self) -> str | None:
        return self._capability

    async def check(
        self,
    ) -> ProviderHealthObservation:
        if self._error is not None:
            raise self._error

        return ProviderHealthObservation(
            provider=self._provider,
            model=self._model,
            capability=self._capability,
            status=self._status,
            observed_at=datetime(
                2026,
                8,
                16,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            latency_ms=125,
            consecutive_failures=0,
            consecutive_successes=1,
        )


def create_runner(
    probes,
) -> ProviderHealthProbeRunner:
    """
    Build the runner using the real application boundary.
    """

    monitor = (
        ProviderHealthMonitorService()
    )

    incident_repository = (
        InMemoryProviderIncidentRepository()
    )

    incident_service = (
        ProviderIncidentService(
            repository=incident_repository
        )
    )

    health_application_service = (
        ProviderHealthApplicationService(
            health_monitor=monitor,
            incident_service=incident_service,
        )
    )

    return ProviderHealthProbeRunner(
        health_application_service=(
            health_application_service
        ),
        probes=probes,
    )


@pytest.mark.asyncio
async def test_runner_submits_healthy_observation() -> None:
    """
    A successful probe must flow through the existing
    ProviderHealthApplicationService.
    """

    runner = create_runner(
        [
            FakeProbe(
                provider="openai",
            )
        ]
    )

    results = await runner.run_all()

    assert len(results) == 1

    result = results[0]

    assert (
        result.observation.provider
        == "openai"
    )

    assert (
        result.observation.status
        == ProviderHealthStatus.HEALTHY
    )

    assert (
        result.observation.latency_ms
        == 125
    )

    assert (
        result.application_result.provider
        == "openai"
    )


@pytest.mark.asyncio
async def test_runner_supports_multiple_providers() -> None:
    """
    Multiple provider probes must remain isolated.
    """

    runner = create_runner(
        [
            FakeProbe(
                provider="openai",
                model="gpt-5-mini",
            ),
            FakeProbe(
                provider="gemini",
                model="gemini-2.5-flash",
            ),
            FakeProbe(
                provider="parallel",
                model=None,
                capability="search",
            ),
            FakeProbe(
                provider="ollama",
                model="gemma4",
            ),
        ]
    )

    results = await runner.run_all()

    assert [
        result.observation.provider
        for result in results
    ] == [
        "openai",
        "gemini",
        "parallel",
        "ollama",
    ]


@pytest.mark.asyncio
async def test_probe_failure_becomes_unavailable_observation() -> None:
    """
    A provider probe exception must become a controlled
    provider-independent unavailable observation.
    """

    runner = create_runner(
        [
            FakeProbe(
                provider="ollama",
                model="gemma4",
                error=RuntimeError(
                    "Ollama service unavailable"
                ),
            )
        ]
    )

    results = await runner.run_all()

    assert len(results) == 1

    observation = (
        results[0].observation
    )

    assert (
        observation.provider
        == "ollama"
    )

    assert (
        observation.status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert (
        observation.error_type
        == "RuntimeError"
    )

    assert (
        observation.error_message
        == "Ollama service unavailable"
    )

    assert (
        observation.consecutive_failures
        == 1
    )


def test_runner_rejects_duplicate_providers() -> None:
    """
    The composition must not accidentally configure the same
    provider twice.
    """

    with pytest.raises(
        ValueError,
        match="Duplicate provider health probe",
    ):
        create_runner(
            [
                FakeProbe(
                    provider="openai"
                ),
                FakeProbe(
                    provider="openai"
                ),
            ]
        )


def test_runner_rejects_empty_provider() -> None:
    """
    Provider identity is mandatory.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Provider health probe provider "
            "cannot be empty"
        ),
    ):
        create_runner(
            [
                FakeProbe(
                    provider="   "
                )
            ]
        )