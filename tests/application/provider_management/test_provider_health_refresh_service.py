"""
Tests for ProviderHealthRefreshService.

The refresh service is an orchestration boundary. These tests verify
that it delegates to the existing ProviderHealthProbeRunner and
returns the runner result unchanged.

No external provider is called.
"""

from __future__ import annotations

import asyncio

from app.application.provider_management.provider_health_refresh_service import (
    ProviderHealthRefreshService,
)


class FakeProbeRunner:
    """Minimal test double for ProviderHealthProbeRunner."""

    def __init__(self) -> None:
        self.calls = 0
        self.result = (
            "provider-health-result",
        )

    async def run_all(self):
        self.calls += 1
        return self.result


def test_refresh_delegates_to_probe_runner() -> None:
    runner = FakeProbeRunner()

    service = ProviderHealthRefreshService(
        probe_runner=runner,
    )

    result = asyncio.run(
        service.refresh()
    )

    assert runner.calls == 1
    assert result == runner.result


def test_refresh_service_rejects_missing_runner() -> None:
    try:
        ProviderHealthRefreshService(
            probe_runner=None,  # type: ignore[arg-type]
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "Provider health probe runner cannot be None."
        )
    else:
        raise AssertionError(
            "Expected ValueError for missing probe runner."
        )