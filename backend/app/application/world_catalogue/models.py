"""Application model for the authoritative Learning World catalogue."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


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
            if not getattr(self, field_name).strip():
                raise ValueError(
                    f"Learning World catalogue {field_name} cannot be empty."
                )

        if self.runtime_world_id is not None and not self.runtime_world_id.strip():
            raise ValueError(
                "runtime_world_id cannot be blank when provided."
            )
