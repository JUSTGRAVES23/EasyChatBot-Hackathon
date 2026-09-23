from __future__ import annotations

from abc import ABC, abstractmethod


class TelegramUpdateIdempotencyPort(ABC):
    """
    Application boundary for durable Telegram inbound-update claiming.

    Persistence details remain infrastructure concerns.
    """

    @abstractmethod
    def claim(self, telegram_update_id: int) -> bool:
        """
        Atomically claim a Telegram update.

        Returns:
            True when this process successfully claimed the update.
            False when the update was already claimed.
        """
        raise NotImplementedError


__all__ = ["TelegramUpdateIdempotencyPort"]
