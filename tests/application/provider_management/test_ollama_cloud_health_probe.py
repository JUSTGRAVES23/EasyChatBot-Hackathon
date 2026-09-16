"""
Unit tests for Ollama Cloud health probe.
"""

import asyncio

import pytest

from app.application.provider_management.provider_health_models import (
    ProviderHealthStatus,
)

from providers.health.ollama_cloud_health_probe import (
    OllamaCloudHealthProbe,
)


def test_cloud_probe_identity() -> None:
    probe = OllamaCloudHealthProbe(
        api_key="test-key",
        model="gpt-oss:120b",
    )

    assert probe.provider == "ollama"
    assert probe.model == "gpt-oss:120b"
    assert probe.capability == "cloud_llm"


def test_cloud_probe_success() -> None:
    probe = OllamaCloudHealthProbe(
        api_key="test-key",
    )

    probe._request_chat = lambda: {
        "model": "gpt-oss:120b",
        "message": {
            "role": "assistant",
            "content": "HEALTH_OK",
        },
        "done": True,
    }

    observation = asyncio.run(
        probe.check()
    )

    assert (
        observation.provider
        == "ollama"
    )

    assert (
        observation.status
        == ProviderHealthStatus.HEALTHY
    )

    assert (
        observation.error_type
        is None
    )

    assert (
        observation.latency_ms
        >= 0
    )


def test_cloud_probe_rejects_empty_response() -> None:
    probe = OllamaCloudHealthProbe(
        api_key="test-key",
    )

    probe._request_chat = lambda: {
        "model": "gpt-oss:120b",
        "message": {
            "role": "assistant",
            "content": "",
        },
        "done": True,
    }

    observation = asyncio.run(
        probe.check()
    )

    assert (
        observation.status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert (
        observation.error_type
        == "ValueError"
    )


def test_cloud_probe_handles_failure() -> None:
    probe = OllamaCloudHealthProbe(
        api_key="test-key",
    )

    def fail():
        raise ConnectionError(
            "Cloud unavailable"
        )

    probe._request_chat = fail

    observation = asyncio.run(
        probe.check()
    )

    assert (
        observation.status
        == ProviderHealthStatus.UNAVAILABLE
    )

    assert (
        observation.error_type
        == "ConnectionError"
    )

    assert (
        observation.consecutive_failures
        == 1
    )


def test_cloud_probe_requires_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="OLLAMA_API_KEY is required",
    ):
        OllamaCloudHealthProbe(
            api_key="",
        )


def test_cloud_probe_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be positive",
    ):
        OllamaCloudHealthProbe(
            api_key="test-key",
            timeout_seconds=0,
        )

