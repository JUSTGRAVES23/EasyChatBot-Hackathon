from __future__ import annotations

from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)


class BetaPrivateChatGate:
    """Authorization boundary for Beta classroom Telegram interactions.

    Telegram transport is allowed to continue only when:
    - the interaction is a private chat; and
    - BetaAccessService confirms the Telegram identity is authorized.

    World onboarding/selection is deliberately outside this gate.

    This is the canonical Beta 1 / Beta 2 Telegram private-chat
    authorization boundary.
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

    async def authorize(
        self,
        *,
        telegram_user_id: int,
        chat_type: str = "private",
    ) -> bool:
        """Return whether the Telegram user may use the private classroom."""

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
        """Require private-chat authorization or raise PermissionError."""

        if chat_type != "private":
            raise PermissionError(
                "Beta classroom access is only available "
                "in a private Telegram chat."
            )

        return await self._access.authorize_private_chat(
            telegram_user_id,
        )


__all__ = [
    "BetaPrivateChatGate",
]