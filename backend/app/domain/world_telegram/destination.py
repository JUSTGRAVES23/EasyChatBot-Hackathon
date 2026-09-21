"""Domain model for a Learning World Telegram destination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class TelegramDestinationType(StrEnum):
    """Supported Telegram community destination types."""

    GROUP = "GROUP"
    CHANNEL = "CHANNEL"


@dataclass(frozen=True, slots=True)
class WorldTelegramDestination:
    """Configuration mapping a Learning World to a Telegram destination."""

    id: UUID
    world_id: UUID
    telegram_chat_id: str
    destination_type: TelegramDestinationType
    enabled: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("destination id must be a UUID.")
        if not isinstance(self.world_id, UUID):
            raise ValueError("world_id must be a UUID.")
        if not self.telegram_chat_id or not self.telegram_chat_id.strip():
            raise ValueError("telegram_chat_id is required.")
        if len(self.telegram_chat_id.strip()) > 255:
            raise ValueError("telegram_chat_id cannot exceed 255 characters.")
        if not isinstance(self.destination_type, TelegramDestinationType):
            raise ValueError("destination_type must be a TelegramDestinationType.")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be a boolean.")
