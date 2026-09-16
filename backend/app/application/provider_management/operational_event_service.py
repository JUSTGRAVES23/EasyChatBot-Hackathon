"""
EasyChatBot AI Operations Center operational event service.

Provides the application boundary for recording operational
facts emitted by Runtime components, provider services, and
future agent frameworks.

Architecture:

Agent / Runtime / Provider Service
                |
                v
       OperationalEventService
                |
                v
       OperationalEventRepository
                |
                v
        Operations Center


Responsibilities:

- accept validated operational events;
- persist events through the repository abstraction;
- retrieve operational events;
- provide a stable application boundary for future
  internal and external agent integrations.

Does NOT:

- execute agents;
- execute providers;
- change Runtime routing;
- approve escalations;
- perform autonomous remediation;
- send notifications;
- access persistence directly.

Operational events remain immutable facts.
"""

from __future__ import annotations

from uuid import UUID

from app.application.provider_management.operational_event import (
    OperationalEvent,
)

from app.application.provider_management.operational_event_repository import (
    OperationalEventRepository,
)


class OperationalEventService:
    """
    Application service for operational event management.

    The service deliberately delegates persistence to the
    repository abstraction and contains no infrastructure logic.
    """

    def __init__(
        self,
        *,
        repository: OperationalEventRepository,
    ) -> None:
        """
        Initialise the operational event service.
        """

        if repository is None:
            raise ValueError(
                "Operational event repository "
                "cannot be None."
            )

        self._repository = repository

    def record(
        self,
        event: OperationalEvent,
    ) -> OperationalEvent:
        """
        Record one operational event.

        The event itself is immutable. The service therefore
        returns the same event after successful persistence.
        """

        if event is None:
            raise ValueError(
                "Operational event cannot be None."
            )

        self._repository.save(event)

        return event

    def get_event(
        self,
        event_id: UUID,
    ) -> OperationalEvent | None:
        """
        Retrieve one operational event by ID.
        """

        if event_id is None:
            raise ValueError(
                "Operational event ID cannot be None."
            )

        return self._repository.get_by_id(
            event_id
        )

    def list_events(
        self,
    ) -> tuple[
        OperationalEvent,
        ...
    ]:
        """
        Return all operational events in repository order.
        """

        return self._repository.get_all()

    def clear(self) -> None:
        """
        Clear operational event state.

        Intended for isolated tests and demonstrations.
        """

        self._repository.clear()