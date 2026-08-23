"""
EasyChatBot AI Operations Center operational events API.

Provides the application-facing read-only boundary for
operational event history.

Architecture:

OperationalEventRepository
        |
        v
OperationalEventService
        |
        v
OperationsCenterOperationalEventsAPI
        |
        v
HTTP Router / Operations Center UI

Responsibilities:

- expose operational event history;
- delegate retrieval to OperationalEventService;
- convert OperationalEvent objects into stable dictionaries;
- keep presentation/API consumers independent from
  internal event dataclasses and enums.

Does NOT:

- create events;
- modify events;
- execute providers;
- execute agents;
- change Runtime routing;
- approve escalations;
- perform autonomous actions.

Operational events remain immutable facts.
"""

from __future__ import annotations

from typing import Any

from app.application.provider_management.operational_event_service import (
    OperationalEventService,
)


class OperationsCenterOperationalEventsAPI:
    """
    Read-only application API for operational event history.
    """

    def __init__(
        self,
        *,
        operational_event_service: OperationalEventService,
    ) -> None:
        """
        Initialise the operational events API.
        """

        if operational_event_service is None:
            raise ValueError(
                "Operational event service "
                "cannot be None."
            )

        self._operational_event_service = (
            operational_event_service
        )

    def list_events(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return all operational events in a
        presentation-safe representation.
        """

        events = (
            self._operational_event_service
            .list_events()
        )

        return [
            self._serialize_event(event)
            for event in events
        ]

    @staticmethod
    def _serialize_event(
        event: Any,
    ) -> dict[str, Any]:
        """
        Convert an OperationalEvent into a stable
        presentation contract.
        """

        return {
            "event_id": str(
                event.event_id
            ),
            "event_type": (
                event.event_type.value
            ),
            "severity": (
                event.severity.value
            ),
            "source": event.source,
            "component": event.component,
            "occurred_at": (
                event.occurred_at.isoformat()
            ),
            "message": event.message,
            "correlation_id": (
                event.correlation_id
            ),
            "metadata": dict(
                event.metadata
            ),
        }