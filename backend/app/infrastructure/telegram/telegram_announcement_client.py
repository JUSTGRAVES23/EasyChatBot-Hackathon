from __future__ import annotations

import os
from typing import Any

from telegram import Bot


class TelegramAnnouncementClient:
    """
    Outbound-only Telegram client for controlled announcements.

    This client is completely separate from TelegramBotRuntime.

    Responsibilities:
    - resolve TELEGRAM_BOT_TOKEN;
    - create an outbound Telegram Bot client lazily;
    - send controlled announcement messages;
    - release client resources.

    This client does NOT:
    - poll Telegram updates;
    - register handlers;
    - start polling;
    - execute classroom conversations;
    - perform administrator authorization;
    - bypass ControlledAnnouncementPublisher.
    """

    def __init__(
        self,
        *,
        token: str | None = None,
    ) -> None:
        self._token = (
            token
            or os.getenv("TELEGRAM_BOT_TOKEN")
        )

        if not self._token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is missing."
            )

        self._bot: Bot | None = None

    def _get_bot(self) -> Bot:
        """
        Return the outbound-only Telegram Bot client.

        The Bot is created lazily and never starts polling.
        """

        if self._bot is None:
            self._bot = Bot(
                token=self._token,
            )

        return self._bot

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        parse_mode: str | None = None,
    ) -> Any:
        """
        Send one outbound Telegram message.

        No Telegram polling is performed.
        """

        bot = self._get_bot()

        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
        )

    async def close(self) -> None:
        """
        Release the outbound Telegram client.
        """

        if self._bot is None:
            return

        await self._bot.shutdown()

        self._bot = None


__all__ = [
    "TelegramAnnouncementClient",
]