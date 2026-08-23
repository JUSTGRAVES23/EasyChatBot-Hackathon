from __future__ import annotations

from backend.app.application.beta_access.beta_access_service import BetaAccessService


class BetaPrivateChatGate:
    """Authorization gate for all Beta classroom interactions."""

    def __init__(self, *, beta_access_service: BetaAccessService) -> None:
        self._access = beta_access_service

    async def authorize(
        self,
        *,
        telegram_user_id: int,
        chat_type: str = "private",
    ) -> bool:
        if chat_type != "private":
            return False

        try:
            await self._access.authorize_private_chat(
                telegram_user_id,
            )
        except (ValueError, PermissionError):
            return False

        return True

    async def require(
        self,
        *,
        telegram_user_id: int,
        chat_type: str = "private",
    ):
        if chat_type != "private":
            raise PermissionError(
                "Beta classroom access is only available in a private Telegram chat."
            )

        return await self._access.authorize_private_chat(
            telegram_user_id,
        )
