"""
AI Runtime provider usage repository.

Defines the persistence boundary for AI Runtime
usage intelligence.

This module does not:

- call providers;
- execute agents;
- calculate costs;
- render dashboards.

Responsibilities:

- store usage events;
- retrieve usage events.

Architecture:

ProviderUsageService
        |
        v
ProviderUsageRepository
        |
        v
Storage implementation


Current implementation:

- in-memory repository.

Future implementations:

- SQLite;
- PostgreSQL;
- analytics warehouse.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.ai_runtime.providers.usage.models import (
    ProviderUsageEvent,
)


class ProviderUsageRepository(ABC):
    """
    Persistence contract for provider usage events.

    Application services depend on this abstraction,
    not directly on storage technology.
    """

    @abstractmethod
    def save(
        self,
        event: ProviderUsageEvent,
    ) -> None:
        """
        Store one provider usage event.
        """

        raise NotImplementedError(
            "Repository save must be implemented."
        )

    @abstractmethod
    def get_all(
        self,
    ) -> list[ProviderUsageEvent]:
        """
        Retrieve stored provider usage events.
        """

        raise NotImplementedError(
            "Repository get_all must be implemented."
        )

    @abstractmethod
    def clear(
        self,
    ) -> None:
        """
        Remove stored usage events.

        Mainly used for testing.
        """

        raise NotImplementedError(
            "Repository clear must be implemented."
        )


class InMemoryProviderUsageRepository(
    ProviderUsageRepository,
):
    """
    In-memory repository implementation.

    Used for:

    - development;
    - testing;
    - hackathon validation.

    This implementation can later be replaced
    by a database-backed repository.
    """

    def __init__(
        self,
    ) -> None:

        self._events: list[
            ProviderUsageEvent
        ] = []

    def save(
        self,
        event: ProviderUsageEvent,
    ) -> None:
        """
        Save a usage event.
        """

        if event is None:
            raise ValueError(
                "Provider usage event cannot be None."
            )

        self._events.append(
            event
        )

    def get_all(
        self,
    ) -> list[ProviderUsageEvent]:
        """
        Return all stored usage events.

        A copy is returned to prevent
        external mutation.
        """

        return list(
            self._events
        )

    def clear(
        self,
    ) -> None:
        """
        Remove all stored usage events.
        """

        self._events.clear()