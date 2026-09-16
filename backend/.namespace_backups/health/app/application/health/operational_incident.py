from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSeverity,
    OperationalSurface,
)


class IncidentStatus(str, Enum):
    """Operational incident lifecycle."""

    DETECTED = "detected"
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class OperationalIncident:
    """
    Correlated operational incident.

    An incident aggregates one or more operational events
    describing the same operational problem.

    This is an application model only. Persistence is deliberately
    handled outside this service.
    """

    incident_id: str
    correlation_id: str
    event_type: OperationalEventType
    surface: OperationalSurface
    severity: OperationalSeverity

    status: IncidentStatus = (
        IncidentStatus.DETECTED
    )

    first_seen: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    last_seen: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    occurrence_count: int = 1

    user_reference: str | None = None
    world_id: str | None = None

    events: list[OperationalEvent] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.incident_id.strip():
            raise ValueError(
                "incident_id cannot be empty."
            )

        if not self.correlation_id.strip():
            raise ValueError(
                "correlation_id cannot be empty."
            )

        if self.occurrence_count < 1:
            raise ValueError(
                "occurrence_count must be at least 1."
            )

    @property
    def is_open(self) -> bool:
        return self.status in {
            IncidentStatus.DETECTED,
            IncidentStatus.OPEN,
            IncidentStatus.ACKNOWLEDGED,
            IncidentStatus.INVESTIGATING,
        }

    def add_event(
        self,
        event: OperationalEvent,
    ) -> None:
        """
        Associate another event with this incident.
        """

        if event.event_type is not self.event_type:
            raise ValueError(
                "Event type does not match incident."
            )

        if event.surface is not self.surface:
            raise ValueError(
                "Event surface does not match incident."
            )

        if (
            event.correlation_id
            != self.correlation_id
        ):
            raise ValueError(
                "Event correlation ID does not "
                "match incident."
            )

        self.events.append(event)

        self.occurrence_count += 1

        if event.occurred_at > self.last_seen:
            self.last_seen = event.occurred_at

        if (
            self.user_reference is None
            and event.user_reference is not None
        ):
            self.user_reference = (
                event.user_reference
            )

        if (
            self.world_id is None
            and event.world_id is not None
        ):
            self.world_id = event.world_id

    def transition(
        self,
        new_status: IncidentStatus,
    ) -> None:
        """
        Apply an explicit lifecycle transition.
        """

        if not isinstance(
            new_status,
            IncidentStatus,
        ):
            raise TypeError(
                "new_status must be IncidentStatus."
            )

        allowed = {
            IncidentStatus.DETECTED: {
                IncidentStatus.OPEN,
                IncidentStatus.ACKNOWLEDGED,
                IncidentStatus.RESOLVED,
            },
            IncidentStatus.OPEN: {
                IncidentStatus.ACKNOWLEDGED,
                IncidentStatus.INVESTIGATING,
                IncidentStatus.RESOLVED,
            },
            IncidentStatus.ACKNOWLEDGED: {
                IncidentStatus.INVESTIGATING,
                IncidentStatus.RESOLVED,
            },
            IncidentStatus.INVESTIGATING: {
                IncidentStatus.RESOLVED,
            },
            IncidentStatus.RESOLVED: {
                IncidentStatus.CLOSED,
            },
            IncidentStatus.CLOSED: set(),
        }

        if new_status not in allowed[self.status]:
            raise ValueError(
                f"Invalid incident transition: "
                f"{self.status.value} -> "
                f"{new_status.value}"
            )

        self.status = new_status

    def as_dict(self) -> dict:
        """
        Return a dashboard-safe incident representation.
        """

        return {
            "incident_id": self.incident_id,
            "correlation_id": self.correlation_id,
            "event_type": self.event_type.value,
            "surface": self.surface.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "first_seen": (
                self.first_seen.isoformat()
            ),
            "last_seen": (
                self.last_seen.isoformat()
            ),
            "occurrence_count": (
                self.occurrence_count
            ),
            "user_reference": (
                self.user_reference
            ),
            "world_id": self.world_id,
            "events": [
                event.as_dict()
                for event in self.events
            ],
        }


__all__ = [
    "IncidentStatus",
    "OperationalIncident",
]