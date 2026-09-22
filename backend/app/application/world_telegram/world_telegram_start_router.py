"""Application routing for Telegram /start World navigation payloads.

W19.7: separates World navigation payloads from the existing Telegram
connection-token onboarding flow.

This component does not authenticate Telegram users, provision World access,
or change a learner's active World.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.world_catalogue.service import LearningWorldCatalogueService


WORLD_START_PREFIX = "world_"


@dataclass(frozen=True, slots=True)
class WorldTelegramRoute:
    """Authoritative World route resolved from a Telegram start payload."""

    world_identifier: str
    runtime_world_id: str


class WorldTelegramStartRouter:
    """Classify and resolve World navigation payloads.

    A payload beginning with ``world_`` is treated as a World navigation
    payload. All other payloads are left for the existing connection-token
    handler.

    This router intentionally has no authentication or persistence side
    effects.
    """

    def __init__(
        self,
        *,
        world_catalogue_service: LearningWorldCatalogueService,
    ) -> None:
        if world_catalogue_service is None:
            raise ValueError("world_catalogue_service cannot be None.")

        self._catalogue = world_catalogue_service

    @staticmethod
    def is_world_payload(payload: str | None) -> bool:
        """Return whether the payload belongs to the W19 World namespace."""
        if payload is None:
            return False

        normalized = payload.strip()
        if not normalized:
            return False

        return normalized.startswith(WORLD_START_PREFIX)

    def resolve(self, payload: str | None) -> WorldTelegramRoute | None:
        """Resolve a World payload or return None for legacy token payloads.

        Unknown, disabled, or runtime-unconfigured Worlds fail closed through
        the existing LearningWorldCatalogueService policy.
        """
        if not self.is_world_payload(payload):
            return None

        normalized = payload.strip()
        world_identifier = normalized[len(WORLD_START_PREFIX) :].strip()

        if not world_identifier:
            raise ValueError("World navigation payload has no World identifier.")

        entry = self._catalogue.get_by_identifier(world_identifier)
        if entry is None:
            raise ValueError(
                f"Learning World not found: {world_identifier}"
            )

        if not entry.enabled:
            raise ValueError(
                f"Learning World is disabled: {entry.identifier}"
            )

        if not entry.runtime_world_id:
            raise ValueError(
                f"Learning World has no runtime configuration: {entry.identifier}"
            )

        # Validate the explicit catalogue -> runtime mapping through the
        # existing authoritative application service. This must not introduce
        # a second mapping in the Telegram layer.
        self._catalogue.resolve_runtime_world(world_identifier)

        return WorldTelegramRoute(
            world_identifier=entry.identifier,
            runtime_world_id=entry.runtime_world_id,
        )


__all__ = [
    "WORLD_START_PREFIX",
    "WorldTelegramRoute",
    "WorldTelegramStartRouter",
]
