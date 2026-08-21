from __future__ import annotations


class BetaTelegramAdapter:
    """
    Thin adapter for python-telegram-bot.

    The adapter deliberately keeps Telegram transport concerns outside
    BetaAccessService.
    """

    def __init__(self, *, start_handler, private_chat_gate):
        self._start_handler = start_handler
        self._private_chat_gate = private_chat_gate

    async def handle_start(self, update, context):
        telegram_user_id = str(update.effective_user.id)
        chat_id = str(update.effective_chat.id)
        args = context.args or []

        token = args[0] if args else ""

        result = self._start_handler.handle(
            token=token,
            telegram_id=telegram_user_id,
            chat_id=chat_id,
        )

        await update.effective_message.reply_text(result.message)

    def is_private_chat_allowed(self, *, user_id: str, chat_type: str) -> bool:
        return self._private_chat_gate.authorize(
            user_id=user_id,
            chat_type=chat_type,
        )
