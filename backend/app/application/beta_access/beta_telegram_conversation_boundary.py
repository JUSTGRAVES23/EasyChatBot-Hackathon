from __future__ import annotations

from typing import Any
import logging


from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)


logger = logging.getLogger(__name__)


class BetaTelegramConversationBoundary:
    """
    Application boundary for Telegram Beta conversations.

    Responsibilities:
    - validate Telegram Beta access
    - resolve learner context
    - delegate clean learner messages

    Does NOT:
    - create LLM providers
    - call Telegram APIs
    - persist conversations
    - inject personal data into messages


    Privacy design:

        Telegram ID
             |
             v
        Authorization
             |
             v
        Clean message
             |
             v
        Conversation Service
             |
             v
        Privacy Event Storage


    Context is NOT inserted into message content.

    Example:

    BEFORE:

        User:
        david@example.com

        World:
        world-fr

        Character:
        Alix

        Message:
        Hello


    AFTER:

        content:
        Hello


        metadata:
        {
            world_id:"world-fr",
            character:"Alix",
            level:"B1"
        }
    """


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


        self._conversation_service = (
            conversation_service
        )

        self._beta_access_service = (
            beta_access_service
        )



    async def handle_message(
        self,
        *,
        telegram_user_id: int,
        message: str,
    ) -> Any:


        if not message or not message.strip():

            raise ValueError(
                "Telegram message cannot be empty."
            )



        #
        # 1. Authorize Telegram user
        #
        # Telegram ID is used ONLY for access control.
        #
        # It is NOT stored in conversation events.
        #

        try:

            context = await (
                self._beta_access_service
                .get_conversation_context(
                    telegram_user_id
                )
            )


        except PermissionError:

            logger.warning(
                "Unauthorized Telegram user=%s",
                telegram_user_id,
            )

            return (
                "Sorry, this Telegram account "
                "is not approved for Beta access."
            )



        #
        # 2. Keep context internal
        #
        # IMPORTANT:
        #
        # Do NOT modify learner message.
        #
        # The Conversation Service will:
        #
        # telegram_user_id
        #        |
        #        v
        # PrivacyIdentifierService
        #        |
        #        v
        # telegram_user_hash
        #
        # and create metadata.
        #

        clean_message = message.strip()



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



        #
        # 3. Delegate clean message
        #
        return await (
            self._conversation_service
            .handle_telegram_message(
                telegram_user_id=telegram_user_id,
                message=clean_message,
            )
        )