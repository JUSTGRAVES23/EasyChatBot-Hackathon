"""Repository port for the Learning World catalogue."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import LearningWorldCatalogueEntry


class LearningWorldCatalogueRepository(Protocol):
    def get_by_identifier(
        self,
        identifier: str,
    ) -> LearningWorldCatalogueEntry | None:
        """Return a catalogue entry by its stable catalogue identifier."""
        ...

    def get_by_id(
        self,
        world_id: UUID,
    ) -> LearningWorldCatalogueEntry | None:
        """Return a catalogue entry by its authoritative World UUID."""
        ...

    def list_all(self) -> tuple[LearningWorldCatalogueEntry, ...]:
        """Return every configured World in the authoritative catalogue."""
        ...