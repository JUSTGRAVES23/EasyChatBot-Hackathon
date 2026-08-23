"""
Tests for provider health composition.

These tests validate composition only. They do not call Ollama Cloud.

The real provider health probe is tested separately in:
    test_ollama_cloud_health_probe.py
"""

from __future__ import annotations

import pytest

from app.application.provider_management.provider_health_composition import (
    DEFAULT_OLLAMA_CLOUD_MODEL,
    create_provider_health_probe_runner,
)


def test_composition_builds_runner_with_ollama_probe() -> None:
    runner = create_provider_health_probe_runner(
        ollama_api_key="test-key",
    )

    probes = runner._probes

    assert len(probes) == 1
    assert probes[0].provider == "ollama"
    assert probes[0].model == DEFAULT_OLLAMA_CLOUD_MODEL
    assert probes[0].capability == "cloud_llm"


def test_composition_accepts_explicit_model() -> None:
    runner = create_provider_health_probe_runner(
        ollama_api_key="test-key",
        ollama_model="gpt-oss:120b",
    )

    probes = runner._probes

    assert len(probes) == 1
    assert probes[0].provider == "ollama"
    assert probes[0].model == "gpt-oss:120b"


def test_composition_requires_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="OLLAMA_API_KEY is required",
    ):
        create_provider_health_probe_runner(
            ollama_api_key="",
        )


def test_composition_rejects_empty_model() -> None:
    with pytest.raises(
        ValueError,
        match="model cannot be empty",
    ):
        create_provider_health_probe_runner(
            ollama_api_key="test-key",
            ollama_model="",
        )


def test_composition_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be positive",
    ):
        create_provider_health_probe_runner(
            ollama_api_key="test-key",
            ollama_timeout_seconds=0,
        )


def test_composition_accepts_injected_services() -> None:
    from app.application.provider_management.provider_health_monitor_service import (
        ProviderHealthMonitorService,
    )
    from app.application.provider_management.provider_incident_service import (
        InMemoryProviderIncidentRepository,
        ProviderIncidentService,
    )

    monitor = ProviderHealthMonitorService()
    incidents = ProviderIncidentService(
        repository=InMemoryProviderIncidentRepository(),
    )

    runner = create_provider_health_probe_runner(
        ollama_api_key="test-key",
        health_monitor=monitor,
        incident_service=incidents,
    )

    assert runner is not None
    assert len(runner._probes) == 1