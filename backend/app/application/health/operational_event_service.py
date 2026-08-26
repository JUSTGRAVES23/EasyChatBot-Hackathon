from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from .operational_event import (
    OperationalEvent,
)
from .operational_incident import (
    IncidentStatus,
    OperationalIncident,
)


class OperationalEventService:
    """
    Application service for operational event correlation
    and incident lifecycle management.

    This service intentionally uses in-memory state for WS-21.9.

    Persistence will be introduced separately once the event
    semantics are proven.

    Responsibilities:
        - accept sanitized operational events
        - correlate repeated events
        - create incidents
        - update occurrence counts
        - maintain incident lifecycle
        - expose dashboard-safe snapshots

    Does NOT:
        - perform remediation
        - send Telegram messages
        - modify production systems
        - execute AI
        - access learner conversation content
    """

    def __init__(
        self,
        *,
        initial_incidents: Iterable[
            OperationalIncident
        ] = (),
    ) -> None:
        self._incidents: dict[
            str,
            OperationalIncident,
        ] = {
            incident.incident_id: incident
            for incident in initial_incidents
        }

        self._correlation_index: dict[
            str,
            str,
        ] = {}

        for incident in self._incidents.values():
            self._correlation_index[
                incident.correlation_id
            ] = incident.incident_id

    def record_event(
        self,
        event: OperationalEvent,
    ) -> OperationalIncident:
        """
        Record an event.

        If an open incident already exists for the
        correlation ID, the event is aggregated into it.

        Otherwise a new incident is created.
        """

        existing_id = (
            self._correlation_index.get(
                event.correlation_id
            )
        )

        if existing_id is not None:
            incident = self._incidents[
                existing_id
            ]

            if not incident.is_open:
                incident = self._create_incident(
                    event
                )
            else:
                incident.add_event(event)

            return incident

        return self._create_incident(event)

    def get_incident(
        self,
        incident_id: str,
    ) -> OperationalIncident | None:
        return self._incidents.get(
            incident_id
        )

    def get_by_correlation_id(
        self,
        correlation_id: str,
    ) -> OperationalIncident | None:
        incident_id = (
            self._correlation_index.get(
                correlation_id
            )
        )

        if incident_id is None:
            return None

        return self._incidents.get(
            incident_id
        )

    def list_incidents(
        self,
        *,
        surface=None,
        status=None,
    ) -> tuple[
        OperationalIncident,
        ...
    ]:
        """
        Return incidents with optional operational filters.
        """

        incidents = tuple(
            self._incidents.values()
        )

        if surface is not None:
            incidents = tuple(
                incident
                for incident in incidents
                if incident.surface is surface
            )

        if status is not None:
            incidents = tuple(
                incident
                for incident in incidents
                if incident.status is status
            )

        return incidents

    def transition_incident(
        self,
        *,
        incident_id: str,
        status: IncidentStatus,
    ) -> OperationalIncident:
        """
        Explicitly transition an incident.
        """

        incident = self._incidents.get(
            incident_id
        )

        if incident is None:
            raise KeyError(
                f"Unknown incident: {incident_id}"
            )

        incident.transition(status)

        return incident

    def count_open_incidents(self) -> int:
        return sum(
            incident.is_open
            for incident
            in self._incidents.values()
        )

    def dashboard_snapshot(self) -> dict:
        """
        Return a dashboard-safe operational snapshot.
        """

        incidents = tuple(
            self._incidents.values()
        )

        return {
            "total_incidents": len(
                incidents
            ),
            "open_incidents": sum(
                incident.is_open
                for incident in incidents
            ),
            "critical_incidents": sum(
                incident.severity.value
                == "critical"
                and incident.is_open
                for incident in incidents
            ),
            "private_classroom_incidents": sum(
                incident.surface.value
                == "private_classroom"
                and incident.is_open
                for incident in incidents
            ),
            "announcement_group_incidents": sum(
                incident.surface.value
                == "announcement_group"
                and incident.is_open
                for incident in incidents
            ),
            "incidents": [
                incident.as_dict()
                for incident in incidents
            ],
        }

    def _create_incident(
        self,
        event: OperationalEvent,
    ) -> OperationalIncident:
        incident = OperationalIncident(
            incident_id=(
                f"incident-{uuid4().hex}"
            ),
            correlation_id=(
                event.correlation_id
            ),
            event_type=event.event_type,
            surface=event.surface,
            severity=event.severity,
            user_reference=(
                event.user_reference
            ),
            world_id=event.world_id,
            events=[event],
        )

        self._incidents[
            incident.incident_id
        ] = incident

        self._correlation_index[
            incident.correlation_id
        ] = incident.incident_id

        return incident


__all__ = [
    "OperationalEventService",
]