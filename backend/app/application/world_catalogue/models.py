"""Application model for the authoritative Learning World catalogue."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.learning.world_access_tier import WorldAccessTier


@dataclass(frozen=True, slots=True)
class LearningWorldCatalogueEntry:
    """Application representation of an authoritative Learning World."""

    id: UUID
    identifier: str
    name: str
    description: str
    language: str
    version: str
    status: str
    enabled: bool
    world_type: str
    learning_domain: str
    runtime_world_id: str | None
    access_tier: WorldAccessTier = WorldAccessTier.NORMAL

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("Learning World catalogue id must be a UUID.")

        for field_name in (
            "identifier",
            "name",
            "version",
            "status",
            "world_type",
            "learning_domain",
        ):
            value = getattr(self, field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Learning World catalogue {field_name} cannot be empty."
                )

        if self.runtime_world_id is not None:
            if not isinstance(self.runtime_world_id, str):
                raise ValueError("runtime_world_id must be a string when provided.")

            if not self.runtime_world_id.strip():
                raise ValueError(
                    "runtime_world_id cannot be blank when provided."
                )

        if not isinstance(self.access_tier, WorldAccessTier):
            raise ValueError(
                "Learning World catalogue access_tier must be a WorldAccessTier."
            )