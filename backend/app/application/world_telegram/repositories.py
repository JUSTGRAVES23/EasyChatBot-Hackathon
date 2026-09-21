"""Repository port for World-to-Telegram destination mappings."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.world_telegram import WorldTelegramDestination


class WorldTelegramDestinationRepository(Protocol):
    """Persistence contract for World Telegram destinations."""

    def get_by_id(
        self,
        destination_id: UUID,
    ) -> WorldTelegramDestination | None:
        """Return a destination by UUID."""
        ...

    def get_by_world_and_chat(
        self,
        *,
        world_id: UUID,
        telegram_chat_id: str,
    ) -> WorldTelegramDestination | None:
        """Return the mapping for a World and Telegram chat."""
        ...

    def list_by_world(
        self,
        world_id: UUID,
    ) -> tuple[WorldTelegramDestination, ...]:
        """Return destinations configured for a World."""
        ...

    def save(
        self,
        destination: WorldTelegramDestination,
    ) -> WorldTelegramDestination:
        """Create or persist a destination."""
        ...

    def delete(
        self,
        destination_id: UUID,
    ) -> bool:
        """Delete a destination and return whether it existed."""
        ...
