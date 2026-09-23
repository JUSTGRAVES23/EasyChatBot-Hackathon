from __future__ import annotations

import logging
import os
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.application.ports.telegram_update_idempotency import (
    TelegramUpdateIdempotencyPort,
)
from app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)


logger = logging.getLogger(__name__)


class TelegramBotRuntime:
    """
    Infrastructure adapter for python-telegram-bot.

    Responsibilities:
    - Telegram application lifecycle;
    - Telegram handler registration;
    - inbound Telegram update idempotency;
    - delegation to BetaTelegramAdapter;
    - exposing the already-created Telegram bot client to
      controlled infrastructure adapters.

    The runtime MUST NOT:
    - perform Beta authorization;
    - execute conversation logic;
    - deliver classroom responses returned by the adapter;
    - create a second Telegram client;
    - bypass the controlled publication boundary.

    IMPORTANT RESPONSE OWNERSHIP:

        Telegram update
              |
              v
        TelegramBotRuntime
              |
              +----> durable update-idempotency claim
              |
              v
        BetaTelegramAdapter
              |
              +----> reply_text()
              |
              v
          response

    The adapter owns Telegram classroom response delivery.

    Therefore the runtime MUST NOT call reply_text() with the
    response returned by the adapter.

    This prevents duplicate Telegram messages.

    IMPORTANT INBOUND IDEMPOTENCY:

    Telegram update_id is the durable inbound processing key.

    A successful claim means this runtime instance owns processing
    of that update.

    A failed claim means the update has already been claimed and
    must not enter the adapter/conversation/AI flow again.

    PUBLICATION CLIENT OWNERSHIP:

        TelegramBotRuntime
              |
              +----> existing Application
                           |
                           +----> existing Bot client
                                      |
                                      v
                         Controlled publication adapters

    The runtime remains the owner of Telegram client creation
    and lifecycle. Consumers receive a reference to the existing
    client through the read-only ``bot`` property.
    """

    def __init__(
        self,
        *,
        adapter: BetaTelegramAdapter,
        conversation_boundary: Any = None,
        telegram_update_idempotency: (
            TelegramUpdateIdempotencyPort | None
        ) = None,
    ) -> None:
        if adapter is None:
            raise ValueError(
                "adapter cannot be None."
            )

        self._adapter = adapter

        # Retained for constructor compatibility with existing
        # composition. Runtime does not execute the boundary.
        self._conversation_boundary = conversation_boundary

        # Durable inbound Telegram update claim.
        #
        # The repository implementation uses the Telegram
        # update_id primary key and PostgreSQL ON CONFLICT
        # protection so concurrent application instances cannot
        # process the same update twice.
        self._telegram_update_idempotency = (
            telegram_update_idempotency
        )

        self._application: Application | None = None
        self._running = False

    # =========================================================
    # Application construction
    # =========================================================

    def build(self) -> Application:
        token = os.getenv(
            "TELEGRAM_BOT_TOKEN"
        )

        if not token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is missing."
            )

        application = (
            Application
            .builder()
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

    # =========================================================
    # Existing Telegram bot client
    # =========================================================

    @property
    def bot(self) -> Any:
        """
        Return the existing Telegram bot client.

        The TelegramBotRuntime remains responsible for creating
        and owning the Telegram Application and its Bot client.

        This property does not create another client and does not
        expose credentials.

        Consumers may use this reference for controlled outbound
        operations such as the announcement publication adapter.

        Raises:
            RuntimeError: If the Telegram application has not yet
                been built.
        """

        if self._application is None:
            raise RuntimeError(
                "Telegram bot runtime has not been built."
            )

        return self._application.bot

    # =========================================================
    # Lifecycle
    # =========================================================

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
                drop_pending_updates=False,
            )

        self._running = True

        logger.info(
            "Telegram bot polling started."
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

    # =========================================================
    # Telegram inbound idempotency
    # =========================================================

    async def _claim_update(
        self,
        update: Update,
    ) -> bool:
        """
        Claim a Telegram update before adapter execution.

        Returns:
            True:
                This update was successfully claimed and may
                continue through the existing adapter flow.

            False:
                This update was already claimed and must stop
                immediately.

        When the idempotency dependency is not configured, the
        runtime preserves the existing behaviour. Production
        composition is expected to provide the durable repository.
        """

        if self._telegram_update_idempotency is None:
            return True

        telegram_update_id = update.update_id

        if telegram_update_id is None:
            return True

        return self._telegram_update_idempotency.claim(
            telegram_update_id
        )

    # =========================================================
    # Telegram handlers
    # =========================================================

    async def _handle_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        # Claim BEFORE entering the adapter.
        #
        # This protects /start updates from duplicate execution
        # in the same way as private classroom messages.
        if not await self._claim_update(update):
            return

        await self._adapter.handle_start(
            update,
            context,
        )

    async def _handle_private_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        if (
            update.effective_user is None
            or update.effective_chat is None
            or update.effective_message is None
        ):
            return

        try:
            # =================================================
            # INBOUND IDEMPOTENCY GATE
            # =================================================
            #
            # The durable claim happens BEFORE:
            #
            #   - authorization;
            #   - conversation boundary;
            #   - private-chat service;
            #   - AI runtime;
            #   - provider execution;
            #   - Telegram response delivery.
            #
            # Duplicate update_ids stop here.
            #

            if not await self._claim_update(update):
                return

            # =================================================
            # SINGLE DELEGATION POINT
            # =================================================
            #
            # BetaTelegramAdapter:
            #
            #   1. validates transport
            #   2. authorizes access
            #   3. invokes conversation boundary
            #   4. sends Telegram response
            #   5. returns response for observation/testing
            #
            # The returned value MUST NOT be sent again.
            #

            await self._adapter.handle_message(
                update,
                context,
            )

        except Exception:
            logger.exception(
                "Unexpected Telegram adapter failure."
            )

            # This is ONLY an infrastructure-level fallback for
            # failures escaping the adapter itself.
            #
            # Normal conversation failures are already contained
            # by BetaTelegramAdapter.
            await update.effective_message.reply_text(
                "EasyChatBot is temporarily unavailable. "
                "Please try again."
            )


__all__ = [
    "TelegramBotRuntime",
]