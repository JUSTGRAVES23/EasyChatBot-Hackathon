"""
EasyChatBot AI Operations Center dashboard models.

Stable read models exposed to the dashboard layer.

This module defines the Operations Center contract.

Architecture:

Provider Health
      |
      v
Operations Center Read Models
      |
      v
Dashboard API
      |
      v
Frontend


Responsibilities:

- define dashboard contracts;
- separate dashboard representation from domain services;
- allow future providers and metrics without breaking API.

Does NOT:

- execute providers;
- calculate health;
- perform routing;
- persist data;
- modify infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.application.provider_management.operations_center_provider_intelligence_service import (
    ProviderIntelligence,
)


class MonitoringStatus(str, Enum):
    """
    Overall Operations Center monitoring state.
    """

    HEALTHY = "healthy"

    ATTENTION_REQUIRED = "attention_required"

    INCIDENT = "incident"


@dataclass(frozen=True)
class ActiveProvider:
    """
    Dashboard representation of one provider.
    """

    provider: str

    model: str

    capabilities: tuple[str, ...]

    active: bool = True

    health_status: str = "unknown"

    latency_ms: int | None = None

    average_latency_ms: int | None = None

    success_rate: float | None = None

    error_rate: float | None = None

    last_check: str | None = None

    consecutive_failures: int = 0

    consecutive_successes: int = 0

    current_incident: bool = False

    incident_id: str | None = None

    estimated_cost: float | None = None

    approved: bool = True

    environment: str = "unknown"


@dataclass(frozen=True)
class OperationsMetrics:
    """
    Execution and platform metrics.
    """

    total_executions: int = 0

    successful_executions: int = 0

    failed_executions: int = 0

    success_rate: float | None = None

    average_latency_ms: float | None = None

    estimated_cost: float = 0.0

    quality_score: float | None = None


@dataclass(frozen=True)
class EscalationSummary:
    """
    Escalation overview displayed in dashboard.
    """

    active: int = 0

    pending: int = 0

    pending_notifications: int = 0

    approved: int = 0

    rejected: int = 0

    total: int = 0


@dataclass(frozen=True)
class MonitoringSummary:
    """
    Monitoring state information.
    """

    status: MonitoringStatus

    message: str

    read_only: bool = True


@dataclass(frozen=True)
class OperationsCenterDashboard:
    """
    Complete Operations Center dashboard contract.
    """

    system_confidence: float

    metrics: OperationsMetrics

    providers: tuple[
        ActiveProvider,
        ...
    ]

    escalations: EscalationSummary

    monitoring: MonitoringSummary

    provider_intelligence: tuple[
        ProviderIntelligence,
        ...
    ] = ()


    #
    # Backward compatibility aliases
    #

    @property
    def active_providers(
        self,
    ) -> tuple[ActiveProvider, ...]:
        return self.providers


    @property
    def monitoring_status(
        self,
    ) -> MonitoringStatus:
        return self.monitoring.status


    @property
    def active_escalations(
        self,
    ) -> int:
        return self.escalations.active


    @property
    def pending_approvals(
        self,
    ) -> int:
        return self.escalations.pending


    @property
    def approved_escalations(
        self,
    ) -> int:
        return self.escalations.approved


    @property
    def rejected_escalations(
        self,
    ) -> int:
        return self.escalations.rejected


    @property
    def pending_notifications(
        self,
    ) -> int:
        return self.escalations.pending_notifications


    @property
    def total_escalations(
        self,
    ) -> int:
        return self.escalations.total