from __future__ import annotations

import logging
from typing import Any

from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)


logger = logging.getLogger(__name__)


class BetaTelegramConversationBoundary:
    """
    Application boundary for Telegram Beta conversations.

    Security order:

        Telegram identity
              ↓
        Message validation
              ↓
        Beta authorization
              ↓
        Authoritative learner context
              ↓
        Conversation service
              ↓
        Safe response
    """

    MAX_TELEGRAM_MESSAGE_LENGTH = 4096

    SAFE_ERROR_RESPONSE = (
        "Sorry, something went wrong while processing your message. "
        "Please try again later."
    )

    UNAUTHORIZED_RESPONSE = (
        "Sorry, this Telegram account is not authorized "
        "and is not approved for Beta access."
    )

    def __init__(
        self,
        *,
        conversation_service: Any,
        beta_access_service: BetaAccessService,
    ) -> None:
        if conversation_service is None:
            raise ValueError(
                "conversation_service cannot be None."
            )

        if beta_access_service is None:
            raise ValueError(
                "beta_access_service cannot be None."
            )

        self._conversation_service = conversation_service
        self._beta_access_service = beta_access_service

    async def handle_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> Any:
        self._validate_telegram_user_id(
            telegram_user_id,
        )

        clean_message = self._validate_message(
            message,
        )

        try:
            context = await (
                self._beta_access_service
                .get_conversation_context(
                    telegram_user_id,
                )
            )

        except PermissionError:
            logger.warning(
                "Unauthorized Telegram user=%s",
                telegram_user_id,
            )

            return self.UNAUTHORIZED_RESPONSE

        logger.info(
            (
                "Beta Telegram context resolved "
                "user=%s world=%s character=%s level=%s"
            ),
            telegram_user_id,
            context.world_id,
            context.character,
            context.level,
        )

        try:
            # Production TelegramConversationService exposes the
            # context-aware method.
            #
            # Existing WS test doubles expose only the original
            # handle_telegram_message() contract. Keeping the
            # compatibility branch prevents validated regression
            # tests from being broken during migration.
            context_handler = getattr(
                self._conversation_service,
                "handle_telegram_message_with_context",
                None,
            )

            if context_handler is not None:
                return await context_handler(
                    telegram_user_id=telegram_user_id,
                    message=clean_message,
                    context=context,
                )

            return await (
                self._conversation_service
                .handle_telegram_message(
                    telegram_user_id=telegram_user_id,
                    message=clean_message,
                )
            )

        except Exception:
            logger.exception(
                "Telegram conversation processing failed "
                "for user=%s.",
                telegram_user_id,
            )

            return self.SAFE_ERROR_RESPONSE

    @classmethod
    def _validate_telegram_user_id(
        cls,
        telegram_user_id: int,
    ) -> None:
        if isinstance(
            telegram_user_id,
            bool,
        ):
            raise ValueError(
                "Telegram user ID must be a positive integer."
            )

        if not isinstance(
            telegram_user_id,
            int,
        ):
            raise TypeError(
                "Telegram user ID must be a positive integer."
            )

        if telegram_user_id <= 0:
            raise ValueError(
                "Telegram user ID must be a positive integer."
            )

    @classmethod
    def _validate_message(
        cls,
        message: str,
    ) -> str:
        # None is semantically an empty Telegram message and has a
        # dedicated validation contract in WS-10.
        if message is None:
            raise ValueError(
                "Telegram message cannot be empty."
            )

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "Telegram message must be a string."
            )

        if not message or not message.strip():
            raise ValueError(
                "Telegram message cannot be empty."
            )

        clean_message = message.strip()

        if len(clean_message) > cls.MAX_TELEGRAM_MESSAGE_LENGTH:
            raise ValueError(
                "Telegram message is too long. "
                "Maximum length is "
                f"{cls.MAX_TELEGRAM_MESSAGE_LENGTH} characters."
            )

        return clean_message


__all__ = [
    "BetaTelegramConversationBoundary",
]