"""Application service for catalogue-to-runtime World resolution."""

from __future__ import annotations

from app.application.uai.world.world_resolver import WorldResolver

from .repositories import LearningWorldCatalogueRepository


class LearningWorldCatalogueService:
    """Apply catalogue policy and delegate runtime resolution to WorldResolver."""

    def __init__(
        self,
        *,
        repository: LearningWorldCatalogueRepository,
        world_resolver: WorldResolver,
    ) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")
        if world_resolver is None:
            raise ValueError("world_resolver cannot be None.")

        self._repository = repository
        self._world_resolver = world_resolver

    def get_by_identifier(self, identifier: str):
        if not identifier or not identifier.strip():
            raise ValueError("catalogue identifier is required.")

        return self._repository.get_by_identifier(identifier.strip())

    def list_all(self):
        """Return all configured Worlds, independent of runtime enabled state."""
        return self._repository.list_all()

    def resolve_runtime_world(self, catalogue_identifier: str):
        entry = self.get_by_identifier(catalogue_identifier)

        if entry is None:
            raise ValueError(
                f"Learning World not found: {catalogue_identifier.strip()}"
            )

        if not entry.enabled:
            raise ValueError(
                f"Learning World is disabled: {entry.identifier}"
            )

        if not entry.runtime_world_id:
            raise ValueError(
                f"Learning World has no runtime configuration: {entry.identifier}"
            )

        return self._world_resolver.resolve(entry.runtime_world_id)
