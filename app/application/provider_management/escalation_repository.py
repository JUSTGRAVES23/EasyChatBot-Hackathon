"""
AI Service Provider Manager escalation repository.

Defines the persistence boundary for provider
operational escalations.

This module does not:

- send emails;
- calculate escalation rules;
- execute providers;
- modify Runtime configuration.

Responsibilities:

- store escalations;
- retrieve escalation history;
- provide a persistence abstraction.

Architecture:

EscalationService
        |
        v
EscalationRepository
        |
        v
Storage Implementation

Current implementation:

- in-memory repository.

Future implementations:

- SQLite;
- PostgreSQL;
- enterprise incident platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.provider_management.models import (
    ProviderEscalation,
)


class EscalationRepository(ABC):
    """
    Persistence contract for provider escalations.

    Application services depend on this abstraction,
    not on a concrete storage implementation.
    """

    @abstractmethod
    def save(
        self,
        escalation: ProviderEscalation,
    ) -> None:
        """
        Store one provider escalation.
        """

        raise NotImplementedError(
            "Escalation save must be implemented."
        )

    @abstractmethod
    def get_all(
        self,
    ) -> list[ProviderEscalation]:
        """
        Retrieve all stored escalations.
        """

        raise NotImplementedError(
            "Escalation get_all must be implemented."
        )

    @abstractmethod
    def get_by_id(
        self,
        escalation_id: str,
    ) -> ProviderEscalation | None:
        """
        Retrieve an escalation by its identifier.
        """

        raise NotImplementedError(
            "Escalation get_by_id must be implemented."
        )

    @abstractmethod
    def clear(
        self,
    ) -> None:
        """
        Clear stored escalations.

        Mainly used by tests.
        """

        raise NotImplementedError(
            "Escalation clear must be implemented."
        )


class InMemoryEscalationRepository(
    EscalationRepository,
):
    """
    In-memory escalation repository.

    Used for:

    - development;
    - testing;
    - hackathon validation.

    It can later be replaced by a persistent
    implementation without changing the service
    contract.
    """

    def __init__(
        self,
    ) -> None:
        self._escalations: list[
            ProviderEscalation
        ] = []

    def save(
        self,
        escalation: ProviderEscalation,
    ) -> None:
        """
        Store one escalation.
        """

        if escalation is None:
            raise ValueError(
                "Escalation cannot be None."
            )

        self._escalations.append(
            escalation
        )

    def get_all(
        self,
    ) -> list[ProviderEscalation]:
        """
        Return all stored escalations.

        A copy is returned to prevent callers
        from mutating repository state directly.
        """

        return list(
            self._escalations
        )

    def get_by_id(
        self,
        escalation_id: str,
    ) -> ProviderEscalation | None:
        """
        Retrieve one escalation by ID.
        """

        if not escalation_id.strip():
            raise ValueError(
                "Escalation id cannot be empty."
            )

        for escalation in self._escalations:
            if (
                escalation.escalation_id
                == escalation_id
            ):
                return escalation

        return None

    def clear(
        self,
    ) -> None:
        """
        Remove all stored escalations.
        """

        self._escalations.clear()