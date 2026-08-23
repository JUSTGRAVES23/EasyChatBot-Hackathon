from __future__ import annotations


class BetaTelegramPrivateChatGate:
    """
    Transport-level gate for Beta Telegram classroom access.

    The gate enforces two conditions:

    1. The Telegram interaction must originate from a private chat.
    2. The associated Beta user must be active.

    This preserves the existing synchronous transport contract used by
    the legacy Telegram integration.
    """

    def __init__(self, *, beta_access_service) -> None:
        self._beta_access_service = beta_access_service

    def authorize(
        self,
        *,
        user_id: str,
        chat_type: str,
    ) -> bool:
        """
        Return True only when the Telegram chat is private and the
        Beta user is active.

        The Beta access service is expected to expose the existing
        synchronous is_active(user_id=...) contract.
        """
        if chat_type != "private":
            return False

        return bool(
            self._beta_access_service.is_active(
                user_id=user_id,
            )
        )