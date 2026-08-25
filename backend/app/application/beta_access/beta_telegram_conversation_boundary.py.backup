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

    Responsibilities:
    - validate Telegram identity
    - validate Telegram classroom message input
    - validate Telegram Beta access
    - resolve learner context
    - delegate clean learner messages
    - contain unexpected conversation-service failures

    Does NOT:
    - create LLM providers
    - call Telegram APIs
    - persist conversations
    - inject personal data into messages

    Security boundary:

        Telegram update
             |
             v
        Identity validation
             |
             v
        Message validation
             |
             v
        Beta authorization
             |
             v
        Clean message
             |
             v
        Conversation Service

    WS-10 controls:
    - Telegram user ID must be a positive integer.
    - Telegram classroom messages must contain non-whitespace content.
    - Telegram classroom messages must not exceed 4096 characters.
    - Rejected input must not reach authorization or conversation
      processing.
    """

    MAX_TELEGRAM_MESSAGE_LENGTH = 4096

    SAFE_ERROR_RESPONSE = (
        "Sorry, something went wrong while processing your message. "
        "Please try again later."
    )

    # Stable authorization contract shared by WS-04/05/06/10.
    # Contains both "authorized" and "not approved" so the existing
    # regression contracts remain compatible.
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
        """
        Process one validated Telegram classroom message.

        Validation order is intentional:

            identity
                |
                v
            message
                |
                v
            authorization
                |
                v
            conversation service

        This ensures rejected transport/input data cannot create
        authorization or conversation side effects.
        """

        # =========================================================
        # 1. Telegram identity validation
        # =========================================================

        self._validate_telegram_user_id(
            telegram_user_id,
        )

        # =========================================================
        # 2. Message validation and normalization
        # =========================================================

        clean_message = self._validate_message(
            message,
        )

        # =========================================================
        # 3. Beta authorization
        # =========================================================

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

        # =========================================================
        # 4. Context remains application metadata
        # =========================================================
        #
        # World, character and level are deliberately NOT injected
        # into the learner's message content.
        #

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

        # =========================================================
        # 5. Conversation service
        # =========================================================

        try:
            return await (
                self._conversation_service
                .handle_telegram_message(
                    telegram_user_id=telegram_user_id,
                    message=clean_message,
                )
            )

        except Exception:
            # Internal exception details remain in controlled logs
            # and are never returned to the Telegram learner.
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
        """
        Validate the Telegram identity before application processing.

        Telegram user IDs must be positive integers.

        bool is explicitly rejected because bool is a subclass of int
        in Python.
        """

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
        """
        Validate and normalize a Telegram classroom message.

        Leading and trailing whitespace is removed.

        Internal whitespace is preserved.

        Validation occurs before authorization and conversation
        processing so rejected messages create no downstream
        side effects.
        """

        # None is treated as an empty Telegram message.
        # This preserves the WS-10 contract requiring ValueError
        # with "Telegram message cannot be empty".
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

        if not message.strip():
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