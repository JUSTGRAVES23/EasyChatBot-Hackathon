from __future__ import annotations

from typing import Any


class TelegramAnnouncementPublisher:
    """Thin infrastructure adapter for the Telegram announcement channel."""

    def __init__(self, *, telegram_client: Any) -> None:
        if telegram_client is None:
            raise ValueError("telegram_client cannot be None.")

        self._telegram_client = telegram_client

    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
    ) -> str:
        if not channel_id.strip():
            raise ValueError("channel_id is required.")

        if not text.strip():
            raise ValueError("text is required.")

        result = await self._telegram_client.send_message(
            chat_id=channel_id,
            text=text,
            parse_mode="Markdown",
        )

        message_id = getattr(result, "message_id", None)
        if message_id is None:
            raise RuntimeError(
                "Telegram publisher did not receive a message identifier."
            )

        return str(message_id)
