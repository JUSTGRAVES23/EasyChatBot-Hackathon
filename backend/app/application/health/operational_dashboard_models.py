from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .health_result import HealthStatus
from .operational_event import OperationalSurface
from .operational_incident import OperationalIncident


@dataclass(frozen=True)
class DashboardDependencyStatus:
    name: str
    status: HealthStatus
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class DashboardIncidentSummary:
    total: int = 0
    open: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "open": self.open,
            "critical": self.critical,
            "high": self.high,
            "medium": self.medium,
            "low": self.low,
            "info": self.info,
        }


@dataclass(frozen=True)
class DashboardOperationalMetrics:
    message_failures: int = 0
    rate_limit_events: int = 0
    abuse_events: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "message_failures": self.message_failures,
            "rate_limit_events": self.rate_limit_events,
            "abuse_events": self.abuse_events,
        }


@dataclass(frozen=True)
class DashboardSurfaceStatus:
    surface: OperationalSurface
    status: HealthStatus
    dependencies: tuple[
        DashboardDependencyStatus,
        ...,
    ] = ()
    incidents: DashboardIncidentSummary = (
        DashboardIncidentSummary()
    )
    metrics: DashboardOperationalMetrics = (
        DashboardOperationalMetrics()
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface.value,
            "status": self.status.value,
            "dependencies": [
                dependency.as_dict()
                for dependency in self.dependencies
            ],
            "incidents": self.incidents.as_dict(),
            "metrics": self.metrics.as_dict(),
        }


@dataclass(frozen=True)
class DashboardIncident:
    """
    Sanitized incident representation for the dashboard.

    Operational references are retained for authorized investigation.
    Learner content and secrets are never part of this model.
    """

    incident_id: str
    correlation_id: str
    surface: OperationalSurface
    severity: str
    status: str
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    user_reference: str | None = None
    world_id: str | None = None

    @classmethod
    def from_incident(
        cls,
        incident: OperationalIncident,
    ) -> "DashboardIncident":
        return cls(
            incident_id=incident.incident_id,
            correlation_id=incident.correlation_id,
            surface=incident.surface,
            severity=incident.severity.value,
            status=incident.status.value,
            first_seen=incident.first_seen,
            last_seen=incident.last_seen,
            occurrence_count=incident.occurrence_count,
            user_reference=incident.user_reference,
            world_id=incident.world_id,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "correlation_id": self.correlation_id,
            "surface": self.surface.value,
            "severity": self.severity,
            "status": self.status,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "occurrence_count": self.occurrence_count,
            "user_reference": self.user_reference,
            "world_id": self.world_id,
        }


@dataclass(frozen=True)
class OperationalDashboardSnapshot:
    """
    Stable application contract consumed by the future
    Operations Center UI/API adapter.
    """

    generated_at: datetime
    overall_status: HealthStatus
    health_score: int

    private_classroom: DashboardSurfaceStatus
    announcement_group: DashboardSurfaceStatus

    incidents: tuple[
        DashboardIncident,
        ...
    ] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "overall": {
                "status": self.overall_status.value,
                "health_score": self.health_score,
            },
            "private_classroom": (
                self.private_classroom.as_dict()
            ),
            "announcement_group": (
                self.announcement_group.as_dict()
            ),
            "incidents": [
                incident.as_dict()
                for incident in self.incidents
            ],
        }


__all__ = [
    "DashboardDependencyStatus",
    "DashboardIncident",
    "DashboardIncidentSummary",
    "DashboardOperationalMetrics",
    "DashboardSurfaceStatus",
    "OperationalDashboardSnapshot",
]