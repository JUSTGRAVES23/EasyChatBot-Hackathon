from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from app.application.beta_access.beta_access_service import (
    BetaAccessService,
)

logger = logging.getLogger(__name__)


class BetaTelegramStartHandler:
    """
    Application-facing handler for /start <token>.

    Rules:
    - /start is valid only in private Telegram chats.
    - A valid Beta connection token is required.
    - Telegram identity binding is delegated to BetaAccessService.
    - Telegram does not select or change Learning Worlds.
    """

    def __init__(
        self,
        *,
        beta_access_service: BetaAccessService,
    ) -> None:
        if beta_access_service is None:
            raise ValueError(
                "beta_access_service cannot be None."
            )

        self._access = beta_access_service

    async def handle(
        self,
        *,
        token: str | None,
        telegram_user_id: int,
        chat_id: int,
        chat_type: str,
        reply: Callable[[str], Any],
    ) -> None:
        if reply is None:
            raise ValueError(
                "reply callback is required."
            )

        if chat_type != "private":
            await self._send_reply(
                reply,
                (
                    "Please open a private chat with the "
                    "EasyChatBot Academy bot to connect "
                    "your classroom."
                ),
            )
            return

        if not token or not token.strip():
            await self._send_reply(
                reply,
                (
                    "Your classroom connection link is "
                    "missing or invalid."
                ),
            )
            return

        try:
            user = await self._access.validate_and_bind(
                token=token.strip(),
                telegram_id=telegram_user_id,
                chat_id=chat_id,
            )

        except (ValueError, PermissionError) as exc:
            logger.warning(
                "Telegram Beta binding rejected "
                "telegram_id=%s reason=%s",
                telegram_user_id,
                exc,
            )

            await self._send_reply(
                reply,
                str(exc),
            )
            return

        # World assignment is authoritative in the Academy
        # application and is never changed from Telegram.
        del user

        await self._send_reply(
            reply,
            (
                "🌱 Welcome to EasyWorld!\n\n"
                "🎓 Your EasyChatBot classroom is now connected.\n\n"
                "Your Worlds are managed through EasyChatBot "
                "Academy. Use the Academy website to onboard "
                "or manage Worlds."
            ),
        )

    @staticmethod
    async def _send_reply(
        reply: Callable[[str], Any],
        message: str,
    ) -> None:
        result = reply(message)

        if inspect.isawaitable(result):
            await result


__all__ = [
    "BetaTelegramStartHandler",
]
