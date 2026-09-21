"""Domain model for learner membership in a World Telegram destination."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class TelegramMembershipStatus(str, Enum):
    """Lifecycle state of a learner's Telegram community membership."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class WorldTelegramMembership:
    """Durable learner membership for a registered World Telegram destination."""

    id: UUID
    destination_id: UUID
    user_id: UUID
    status: TelegramMembershipStatus
    joined_at: datetime
    left_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise ValueError("membership id must be a UUID.")
        if not isinstance(self.destination_id, UUID):
            raise ValueError("destination_id must be a UUID.")
        if not isinstance(self.user_id, UUID):
            raise ValueError("user_id must be a UUID.")
        if not isinstance(self.status, TelegramMembershipStatus):
            raise ValueError("status must be a TelegramMembershipStatus.")
        if self.status is TelegramMembershipStatus.ACTIVE and self.left_at is not None:
            raise ValueError("active membership cannot have left_at.")
