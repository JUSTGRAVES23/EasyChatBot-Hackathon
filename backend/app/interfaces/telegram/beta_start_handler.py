from __future__ import annotations

import logging
from typing import Callable, Awaitable

from app.application.beta_access.beta_access_service import BetaAccessService

logger = logging.getLogger(__name__)


class BetaTelegramStartHandler:
    """Adapter for /start <token>. Only private chats may bind Beta users."""

    def __init__(
        self,
        *,
        beta_access_service: BetaAccessService,
        reply: Callable[[str, object], Awaitable[None]],
    ) -> None:
        self._access = beta_access_service
        self._reply = reply

    async def handle(
        self,
        *,
        token: str | None,
        telegram_user_id: int,
        chat_id: int,
        chat_type: str,
    ) -> None:
        if chat_type != "private":
            await self._reply(
                "Please open a private chat with the Academy bot to connect your classroom.",
                None,
            )
            return

        if not token:
            await self._reply(
                "Your classroom connection link is missing or invalid.",
                None,
            )
            return

        try:
            user = await self._access.validate_and_bind(
                token=token,
                telegram_id=telegram_user_id,
                chat_id=chat_id,
            )
        except (ValueError, PermissionError) as exc:
            logger.warning(
                "Telegram Beta binding rejected telegram_id=%s reason=%s",
                telegram_user_id,
                exc,
            )
            await self._reply(str(exc), None)
            return

        await self._reply(
            (
                "Welcome to EasyChatBot Academy. "
                f"Your classroom is connected to World '{user.active_world_id}'."
            ),
            user,
        )
