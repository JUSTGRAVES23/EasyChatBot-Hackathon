from __future__ import annotations

from typing import Any


class BetaTelegramAdapter:
    """
    Thin Telegram transport adapter for Beta 1.

    Flow:
        Telegram Update
            -> BetaTelegramStartHandler / BetaPrivateChatGate
            -> application boundary

    This adapter contains no Beta business rules and no LLM/provider logic.
    """

    def __init__(
        self,
        *,
        start_handler: Any,
        private_chat_gate: Any,
        conversation_boundary: Any | None = None,
    ) -> None:
        self._start_handler = start_handler
        self._private_chat_gate = private_chat_gate
        self._conversation_boundary = conversation_boundary

    async def handle_start(self, update: Any, context: Any) -> None:
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message

        if user is None or chat is None or message is None:
            return

        token_args = getattr(context, "args", None) or []
        token = token_args[0] if token_args else None

        reply = self._build_reply(message)

        await self._start_handler.handle(
            token=token,
            telegram_user_id=int(user.id),
            chat_id=int(chat.id),
            chat_type=str(chat.type),
        )

    async def authorize_message(self, update: Any) -> bool:
        """
        Gate a normal Telegram message.

        Group/channel traffic is rejected before reaching the
        conversation application boundary.
        """
        user = update.effective_user
        chat = update.effective_chat

        if user is None or chat is None:
            return False

        return await self._private_chat_gate.authorize(
            telegram_user_id=int(user.id),
            chat_type=str(chat.type),
        )

    async def handle_message(self, update: Any, context: Any) -> Any:
        """
        Authorize first, then delegate to the application boundary.

        The adapter does not call an LLM/provider directly.
        """
        allowed = await self.authorize_message(update)

        if not allowed:
            return None

        if self._conversation_boundary is None:
            raise RuntimeError(
                "Conversation application boundary is not configured."
            )

        user = update.effective_user
        message = update.effective_message

        if user is None or message is None:
            return None

        text = getattr(message, "text", None)
        if not text:
            return None

        return await self._conversation_boundary.handle_message(
            telegram_user_id=int(user.id),
            message=text,
        )

    @staticmethod
    def _build_reply(message: Any) -> Any:
        return message
