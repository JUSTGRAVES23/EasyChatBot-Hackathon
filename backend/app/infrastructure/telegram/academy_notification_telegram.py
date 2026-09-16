from __future__ import annotations

from typing import Any


class ExistingBotTelegramNotificationSender:
    """Outbound adapter around the existing Telegram Bot instance.

    No Bot is created here. The composition root injects the existing
    `TelegramBotRuntime.bot`.
    """

    def __init__(self, bot: Any) -> None:
        if bot is None:
            raise ValueError("bot cannot be None.")
        self._bot = bot

    async def send(
        self,
        *,
        chat_id: str,
        text: str,
        portal_url: str,
    ) -> dict:
        if not chat_id.strip():
            raise ValueError("chat_id cannot be empty.")
        if not portal_url.strip():
            raise ValueError("portal_url cannot be empty.")

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚀 Continue Learning", url=portal_url)]]
        )

        message = await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=markup,
        )

        return {
            "provider": "telegram",
            "status": "accepted",
            "message_id": getattr(message, "message_id", None),
        }
