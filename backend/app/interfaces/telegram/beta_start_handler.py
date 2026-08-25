from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)

logger = logging.getLogger(__name__)


class BetaTelegramStartHandler:
    """Application-facing handler for ``/start <token>``.

    Beta 1 rules:

    - /start is only valid in a private Telegram chat.
    - A valid Beta access token is required.
    - Telegram identity binding is delegated to BetaAccessService.
    - World onboarding/selection is never performed by Telegram.
    - The reply boundary accepts the established ``reply(text)`` contract.
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
        """Handle a Telegram /start request.

        The reply callable may be synchronous or asynchronous.
        """

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

        # --------------------------------------------------------------
        # Important Beta 1 boundary
        # --------------------------------------------------------------
        #
        # Telegram does NOT onboard, select, change, or switch Worlds.
        #
        # World assignment is authoritative in the EasyChatBot
        # application.
        #
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
        """Execute synchronous or asynchronous reply callbacks."""

        result = reply(message)

        if inspect.isawaitable(result):
            await result


__all__ = [
    "BetaTelegramStartHandler",
]