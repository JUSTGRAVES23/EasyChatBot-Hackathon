"""
EasyChatBot AI Operations Center provider intelligence models.

Stable read models for provider operational intelligence.

Architecture:

Provider Health History
        |
        v
Provider Intelligence Service
        |
        v
ProviderIntelligence
        |
        v
Operations Center Dashboard


Responsibilities:

- define provider intelligence contracts;
- expose dashboard-safe operational metrics;
- separate intelligence representation from health execution.

Does NOT:

- execute providers;
- call external APIs;
- perform health probes;
- modify Runtime routing;
- perform remediation;
- persist data.

This is a read-only operational intelligence model.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderIntelligence:
    """
    Dashboard-safe provider intelligence read model.

    Represents calculated operational information
    derived from provider health history.

    It is not a live provider execution result.
    """

    provider: str

    model: str | None

    capability: str | None

    availability_percentage: float

    average_latency_ms: float | None

    total_checks: int

    successful_checks: int

    failed_checks: int

    health_trend: str


__all__ = [
    "ProviderIntelligence",
]