"""
WS-21.18 Announcement Group Operations application API.

Read-only, fresh operational detail for the Announcement Group surface.

The API deliberately reuses the existing OperationalDashboardService
and the authoritative OperationalEventService supplied by the Operations
Center composition root.

No second incident/event store is created.

Security boundary:
    Raw operational event metadata is never exposed through this API.
    Only explicitly approved operational metadata keys are returned.
"""

from __future__ import annotations

from typing import Any

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.operational_event import (
    OperationalSurface,
)
from app.application.health.operational_event_service import (
    OperationalEventService,
)
from app.application.health.operational_incident import (
    OperationalIncident,
)


# Operational metadata explicitly approved for the Operations Center UI.
#
# Sensitive learner content, prompts, AI responses, credentials, tokens,
# and arbitrary provider payloads are deliberately excluded.
SAFE_EVENT_METADATA_KEYS = frozenset(
    {
        "safe_status",
    }
)


class AnnouncementGroupOperationsAPI:
    """Read-only application boundary for WS-21.18."""

    def __init__(
        self,
        *,
        dashboard_service: OperationalDashboardService,
        event_service: OperationalEventService | None = None,
    ) -> None:
        if dashboard_service is None:
            raise ValueError(
                "dashboard_service cannot be None."
            )

        self._dashboard_service = dashboard_service

        self._event_service = (
            event_service
            if event_service is not None
            else dashboard_service.event_service
        )

    async def get_details(self) -> dict[str, Any]:
        """
        Build a fresh Announcement Group snapshot.

        Every request performs fresh dependency health evaluation and reads
        the current operational incident/event state.
        """

        snapshot = (
            await self._dashboard_service.create_dashboard_snapshot()
        )

        incidents = self._event_service.list_incidents(
            surface=OperationalSurface.ANNOUNCEMENT_GROUP,
        )

        events = tuple(
            event
            for incident in incidents
            for event in incident.events
        )

        return {
            "generated_at": snapshot.generated_at.isoformat(),
            "surface": "announcement_group",
            "status": (
                snapshot.announcement_group.status.value
            ),
            "health_score": snapshot.health_score,
            "dependencies": [
                dependency.as_dict()
                for dependency
                in snapshot.announcement_group.dependencies
            ],
            "metrics": (
                snapshot.announcement_group.metrics.as_dict()
            ),
            "incidents": {
                "summary": (
                    snapshot.announcement_group
                    .incidents
                    .as_dict()
                ),
                "items": [
                    _incident_to_dict(incident)
                    for incident in incidents
                ],
            },
            "events": [
                _event_to_dict(event)
                for event in events
            ],
        }


def _incident_to_dict(
    incident: OperationalIncident,
) -> dict[str, Any]:
    """
    Return an existing incident in dashboard-safe form.

    Raw event metadata is deliberately not serialized.
    """

    return {
        "incident_id": incident.incident_id,
        "correlation_id": incident.correlation_id,
        "event_type": incident.event_type.value,
        "surface": incident.surface.value,
        "severity": incident.severity.value,
        "status": incident.status.value,
        "first_seen": incident.first_seen.isoformat(),
        "last_seen": incident.last_seen.isoformat(),
        "occurrence_count": incident.occurrence_count,
        "user_reference": incident.user_reference,
        "world_id": incident.world_id,
        "events": [
            _event_to_dict(event)
            for event in incident.events
        ],
    }


def _event_to_dict(event) -> dict[str, Any]:
    """
    Serialize an operational event through an explicit security boundary.

    Do not call event.as_dict() here because that currently includes the
    complete raw metadata dictionary.
    """

    metadata = getattr(event, "metadata", {}) or {}

    safe_metadata = {
        key: metadata[key]
        for key in SAFE_EVENT_METADATA_KEYS
        if key in metadata
    }

    return {
        "event_type": event.event_type.value,
        "surface": event.surface.value,
        "correlation_id": event.correlation_id,
        "severity": event.severity.value,
        "occurred_at": event.occurred_at.isoformat(),
        "user_reference": event.user_reference,
        "world_id": event.world_id,
        "metadata": safe_metadata,
    }


__all__ = [
    "AnnouncementGroupOperationsAPI",
]




