"""Application service for World-to-Telegram destination management."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.world_catalogue.repositories import (
    LearningWorldCatalogueRepository,
)
from app.domain.world_telegram import (
    TelegramDestinationType,
    WorldTelegramDestination,
)

from .repositories import WorldTelegramDestinationRepository


class WorldTelegramDestinationService:
    """Coordinate World Telegram destination configuration."""

    def __init__(
        self,
        *,
        repository: WorldTelegramDestinationRepository,
        world_catalogue_repository: LearningWorldCatalogueRepository,
    ) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")
        if world_catalogue_repository is None:
            raise ValueError("world_catalogue_repository cannot be None.")

        self._repository = repository
        self._world_catalogue_repository = world_catalogue_repository

    def register_destination(
        self,
        *,
        world_id: UUID,
        telegram_chat_id: str,
        destination_type: TelegramDestinationType,
        enabled: bool = True,
    ) -> WorldTelegramDestination:
        if not isinstance(world_id, UUID):
            raise ValueError("world_id must be a UUID.")

        if not telegram_chat_id or not telegram_chat_id.strip():
            raise ValueError("telegram_chat_id is required.")

        if not isinstance(destination_type, TelegramDestinationType):
            raise ValueError("destination_type is invalid.")

        normalized_chat_id = telegram_chat_id.strip()

        world = self._world_catalogue_repository.get_by_id(world_id)
        if world is None:
            raise ValueError(f"Learning World '{world_id}' does not exist.")

        existing = self._repository.get_by_world_and_chat(
            world_id=world_id,
            telegram_chat_id=normalized_chat_id,
        )
        if existing is not None:
            raise ValueError(
                "Telegram destination is already registered for this World."
            )

        now = datetime.now(timezone.utc)

        destination = WorldTelegramDestination(
            id=uuid4(),
            world_id=world.id,
            telegram_chat_id=normalized_chat_id,
            destination_type=destination_type,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )

        return self._repository.save(destination)

    def get_destination(
        self,
        destination_id: UUID,
    ) -> WorldTelegramDestination | None:
        return self._repository.get_by_id(destination_id)

    def list_destinations(
        self,
        world_id: UUID,
    ) -> tuple[WorldTelegramDestination, ...]:
        if not isinstance(world_id, UUID):
            raise ValueError("world_id must be a UUID.")

        return self._repository.list_by_world(world_id)

    def set_enabled(
        self,
        *,
        destination_id: UUID,
        enabled: bool,
    ) -> WorldTelegramDestination:
        destination = self._repository.get_by_id(destination_id)

        if destination is None:
            raise ValueError(
                f"Telegram destination '{destination_id}' does not exist."
            )

        updated = WorldTelegramDestination(
            id=destination.id,
            world_id=destination.world_id,
            telegram_chat_id=destination.telegram_chat_id,
            destination_type=destination.destination_type,
            enabled=enabled,
            created_at=destination.created_at,
            updated_at=datetime.now(timezone.utc),
        )

        return self._repository.save(updated)

    def delete_destination(
        self,
        destination_id: UUID,
    ) -> bool:
        return self._repository.delete(destination_id)