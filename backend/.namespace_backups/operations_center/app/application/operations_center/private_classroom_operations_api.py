"""
WS-21.17 Private Classroom Operations application API.

Read-only, fresh operational detail for the Private Classroom surface.

The API reuses the existing Operations Center dashboard service and
operational incident/event abstractions.

No second monitoring model is created.
No infrastructure is accessed directly.
No operational side effects are performed.
"""

from __future__ import annotations

from typing import Any

from app.application.health.operational_dashboard_service import (
    OperationalDashboardService,
)
from app.application.health.operational_incident import (
    OperationalIncident,
)


_PRIVATE_CLASSROOM_SURFACE = "private_classroom"


class PrivateClassroomOperationsAPI:
    """Read-only application boundary for WS-21.17."""

    def __init__(
        self,
        *,
        dashboard_service: OperationalDashboardService,
    ) -> None:
        if dashboard_service is None:
            raise ValueError(
                "dashboard_service cannot be None."
            )

        self._dashboard_service = dashboard_service

    async def get_details(self) -> dict[str, Any]:
        """
        Build a fresh Private Classroom operational snapshot.

        Dependency probes are executed by the existing dashboard service.

        Incident/event state is read from the dashboard service's
        existing application-owned event abstraction.
        """

        snapshot = (
            await self._dashboard_service.create_dashboard_snapshot()
        )

        # Retrieve the authoritative current incident collection.
        #
        # We intentionally do not pass OperationalSurface here because
        # the repository can be reached through multiple legacy package
        # namespaces in the current repository. Filtering by the stable
        # serialized surface value avoids enum identity mismatches.
        all_incidents = self._dashboard_service.list_incidents()

        incidents = tuple(
            incident
            for incident in all_incidents
            if _surface_value(incident.surface)
            == _PRIVATE_CLASSROOM_SURFACE
        )

        events = tuple(
            event
            for incident in incidents
            for event in incident.events
        )

        return {
            "generated_at": snapshot.generated_at.isoformat(),
            "surface": _PRIVATE_CLASSROOM_SURFACE,
            "status": snapshot.private_classroom.status.value,
            "health_score": snapshot.health_score,
            "dependencies": [
                dependency.as_dict()
                for dependency
                in snapshot.private_classroom.dependencies
            ],
            "metrics": (
                snapshot.private_classroom
                .metrics
                .as_dict()
            ),
            "incidents": {
                "summary": (
                    snapshot.private_classroom
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


def _surface_value(surface: Any) -> str:
    """
    Return a stable surface value.

    Supports both Enum instances and string-compatible values.
    """

    value = getattr(surface, "value", surface)

    return str(value).lower()


def _incident_to_dict(
    incident: OperationalIncident,
) -> dict[str, Any]:
    """
    Return a dashboard-safe incident representation.
    """

    return {
        "incident_id": incident.incident_id,
        "correlation_id": incident.correlation_id,
        "event_type": incident.event_type.value,
        "surface": _surface_value(incident.surface),
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


def _event_to_dict(event: Any) -> dict[str, Any]:
    """
    Return a sanitized operational event.

    Only explicitly approved operational metadata is exposed.
    Learner content, prompts, responses and secrets are excluded.
    """

    payload = event.as_dict()

    metadata = payload.get("metadata", {})

    if not isinstance(metadata, dict):
        metadata = {}

    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key in {
            "safe_status",
            "status",
            "reason",
            "error_code",
            "error_type",
            "dependency",
            "provider",
            "model",
            "capability",
        }
    }

    payload["metadata"] = safe_metadata

    return payload


__all__ = [
    "PrivateClassroomOperationsAPI",
]


