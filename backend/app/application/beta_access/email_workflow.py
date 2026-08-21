from __future__ import annotations

from typing import Protocol

from .beta_access_service import BetaAccessService


class BetaEmailSender(Protocol):
    async def send_beta_invitation(
        self,
        *,
        email: str,
        classroom_url: str,
    ) -> None: ...


class BetaTelegramInvitationService:
    """Creates the one-time Telegram deep link and sends the invitation email."""

    def __init__(
        self,
        *,
        beta_access_service: BetaAccessService,
        email_sender: BetaEmailSender,
        telegram_bot_username: str,
    ) -> None:
        if not telegram_bot_username:
            raise ValueError("telegram_bot_username is required.")
        self._access = beta_access_service
        self._email_sender = email_sender
        self._bot_username = telegram_bot_username.lstrip("@")

    async def send_invitation(self, *, user_id: str) -> str:
        raw_token, _ = await self._access.create_connection_token(user_id)
        classroom_url = (
            f"https://t.me/{self._bot_username}?start={raw_token}"
        )

        user = await self._access._require_user(user_id)
        await self._email_sender.send_beta_invitation(
            email=user.email,
            classroom_url=classroom_url,
        )
        return classroom_url
