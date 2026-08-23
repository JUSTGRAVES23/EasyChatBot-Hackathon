from __future__ import annotations

import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


from backend.app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)

from backend.app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)


logger = logging.getLogger(__name__)


class TelegramBotRuntime:
    """
    Infrastructure adapter for python-telegram-bot.

    Responsibilities:
    - create Telegram Application
    - register Telegram handlers
    - start Telegram polling
    - route Telegram transport events

    Does NOT:
    - contain Beta business rules
    - validate users directly
    - create LLM providers
    - execute AI directly
    """


    def __init__(
        self,
        *,
        adapter: BetaTelegramAdapter,
        conversation_boundary: BetaTelegramConversationBoundary,
    ) -> None:

        self._adapter = adapter
        self._conversation_boundary = conversation_boundary

        self._application: Application | None = None
        self._running = False



    def build(self) -> Application:

        token = os.getenv(
            "TELEGRAM_BOT_TOKEN"
        )

        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is missing."
            )


        application = (
            Application.builder()
            .token(token)
            .build()
        )


        application.add_handler(
            CommandHandler(
                "start",
                self._handle_start,
            )
        )


        application.add_handler(
            MessageHandler(
                filters.ChatType.PRIVATE
                & filters.TEXT
                & ~filters.COMMAND,
                self._handle_private_message,
            )
        )


        self._application = application


        logger.info(
            "Telegram bot runtime created."
        )


        return application



    async def start(self) -> None:

        if self._running:

            logger.warning(
                "Telegram runtime already running."
            )

            return


        if self._application is None:

            self.build()


        assert self._application is not None


        await self._application.initialize()


        await self._application.start()


        if self._application.updater is not None:

            await self._application.updater.start_polling(
                drop_pending_updates=False
            )


        self._running = True


        logger.info(
            "Telegram bot polling started."
        )


        logger.info(
            "Telegram bot runtime started."
        )



    async def stop(self) -> None:

        if self._application is None:

            return


        if (
            self._application.updater is not None
            and self._running
        ):

            await self._application.updater.stop()


        await self._application.stop()


        await self._application.shutdown()


        self._running = False


        logger.info(
            "Telegram bot runtime stopped."
        )



    async def _handle_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:


        logger.info(
            "START command received."
        )


        await self._adapter.handle_start(
            update,
            context,
        )



    async def _handle_private_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:


        logger.warning(
            "PRIVATE MESSAGE HANDLER TRIGGERED"
        )


        if (
            update.effective_user is None
            or update.effective_chat is None
            or update.effective_message is None
        ):

            logger.warning(
                "Telegram update missing required fields."
            )

            return



        if update.effective_chat.type != "private":

            logger.info(
                "Ignoring non-private chat type=%s",
                update.effective_chat.type,
            )

            return



        message = (
            update.effective_message.text
        )


        if not message:

            return



        telegram_user_id = (
            update.effective_user.id
        )


        logger.info(
            "Private Telegram message received user=%s message=%s",
            telegram_user_id,
            message,
        )



        try:

            response = await (
                self._conversation_boundary.handle_message(
                    telegram_user_id=telegram_user_id,
                    message=message,
                )
            )


        except Exception:

            logger.exception(
                "Telegram conversation processing failed."
            )


            await update.effective_message.reply_text(
                "⚠️ EasyChatBot is temporarily unavailable. Please try again."
            )


            return



        await update.effective_message.reply_text(
            str(response)
        )