from __future__ import annotations


class BetaTelegramPrivateChatGate:
    """
    Transport-level gate.

    Beta classroom access is permitted only from a Telegram private chat.
    """

    def __init__(self, *, beta_access_service):
        self._beta_access_service = beta_access_service

    def authorize(
        self,
        *,
        user_id: str,
        chat_type: str,
    ) -> bool:
        if chat_type != "private":
            return False

        return self._beta_access_service.is_active(user_id=user_id)
