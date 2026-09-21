"""Domain contracts for World-to-Telegram community mappings."""

from .destination import TelegramDestinationType, WorldTelegramDestination
from .membership import TelegramMembershipStatus, WorldTelegramMembership

__all__ = [
    "TelegramDestinationType",
    "WorldTelegramDestination",
    "TelegramMembershipStatus",
    "WorldTelegramMembership",
]
