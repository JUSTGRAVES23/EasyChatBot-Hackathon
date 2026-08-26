from __future__ import annotations

import os
from typing import Any

from telegram import Bot


class TelegramAnnouncementClient:
    """
    Outbound-only Telegram client for controlled announcements.

    Responsibilities:
    - authenticate using TELEGRAM_BOT_TOKEN;
    - send outbound announcement messages;
    - provide controlled Telegram transport.

    This client MUST NOT:
    - start Telegram polling;
    - register Telegram handlers;
    - execute classroom conversations;
    - perform authorization;
    - bypass ControlledAnnouncementPublisher.

    The classroom Telegram runtime owns inbound update polling.
    This client is strictly outbound.
    """

    def __init__(
        self,
        *,
        token: str | None = None,
    ) -> None:
        resolved_token = (
            token
            or os.getenv("TELEGRAM_BOT_TOKEN")
        )

        if not resolved_token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is missing."
            )

        self._bot = Bot(
            token=resolved_token,
        )

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
    ) -> Any:
        """
        Send one outbound Telegram announcement.

        This operation does not start polling and does not
        interact with the inbound Telegram update lifecycle.
        """

        return await self._bot.send_message(
            chat_id=chat_id,
            text=text,
        )

    async def close(self) -> None:
        """
        Release the underlying Telegram client resources.
        """

        await self._bot.shutdown()


__all__ = [
    "TelegramAnnouncementClient",
]