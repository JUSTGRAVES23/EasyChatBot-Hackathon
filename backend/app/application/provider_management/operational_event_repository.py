"""
EasyChatBot AI Operations Center operational event repository.

Provides the persistence boundary for immutable operational
events.

Architecture:

OperationalEvent
        |
        v
OperationalEventRepository
        |
        v
In-Memory / Future Persistent Store


Responsibilities:

- define the repository contract;
- store operational events;
- retrieve events deterministically;
- keep persistence concerns outside the event model.

Does NOT:

- interpret event meaning;
- execute agents;
- execute providers;
- change Runtime routing;
- create autonomous actions;
- send notifications.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.provider_management.operational_event import (
    OperationalEvent,
)


class OperationalEventRepository(ABC):
    """
    Persistence boundary for operational events.
    """

    @abstractmethod
    def save(
        self,
        event: OperationalEvent,
    ) -> None:
        """
        Persist one operational event.
        """

        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        event_id,
    ) -> OperationalEvent | None:
        """
        Return an event by its unique identifier.
        """

        raise NotImplementedError

    @abstractmethod
    def get_all(
        self,
    ) -> tuple[
        OperationalEvent,
        ...
    ]:
        """
        Return all stored events in deterministic order.
        """

        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """
        Clear repository state.

        Intended primarily for isolated tests and demonstrations.
        """

        raise NotImplementedError


class InMemoryOperationalEventRepository(
    OperationalEventRepository
):
    """
    In-memory operational event repository.

    This implementation is intentionally small and deterministic.
    It can later be replaced by a persistent implementation
    without changing the application service contract.
    """

    def __init__(self) -> None:
        self._events: dict[
            object,
            OperationalEvent,
        ] = {}

    def save(
        self,
        event: OperationalEvent,
    ) -> None:
        """
        Store an operational event.
        """

        if event is None:
            raise ValueError(
                "Operational event cannot be None."
            )

        self._events[
            event.event_id
        ] = event

    def get_by_id(
        self,
        event_id,
    ) -> OperationalEvent | None:
        """
        Retrieve an event by ID.
        """

        if event_id is None:
            raise ValueError(
                "Operational event ID cannot be None."
            )

        return self._events.get(
            event_id
        )

    def get_all(
        self,
    ) -> tuple[
        OperationalEvent,
        ...
    ]:
        """
        Return events ordered by occurrence time and event ID.
        """

        return tuple(
            sorted(
                self._events.values(),
                key=lambda event: (
                    event.occurred_at,
                    str(event.event_id),
                ),
            )
        )

    def clear(self) -> None:
        """
        Remove all stored events.
        """

        self._events.clear()