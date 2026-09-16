from __future__ import annotations

import logging
from typing import Any

from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from app.interfaces.telegram.private_chat_gate import (
    BetaPrivateChatGate,
)


logger = logging.getLogger(__name__)


class BetaTelegramAdapter:
    """
    Telegram transport adapter for the Beta private classroom.

    Responsibilities:
    - handle Telegram transport metadata;
    - enforce private-chat-only classroom access;
    - authorize Telegram identity through BetaPrivateChatGate;
    - forward authorized messages to BetaTelegramConversationBoundary;
    - deliver safe user-facing Telegram responses.

    Response ownership:

        Conversation Boundary
                |
                v
             response
                |
                v
        BetaTelegramAdapter
                |
                +----> Telegram reply_text()
                |
                v
             response

    IMPORTANT:

    The adapter is the SINGLE owner of classroom Telegram response
    delivery.

    The returned response is provided to the direct caller for
    testing, observability, and application-level inspection.

    The caller MUST NOT send the returned response to Telegram again.

    This adapter MUST NOT:
    - call an LLM/provider directly;
    - access persistence directly;
    - modify Beta user state directly;
    - bypass BetaAccessService;
    - process group/channel messages through the AI path.
    """

    def __init__(
        self,
        *,
        start_handler: Any,
        private_chat_gate: BetaPrivateChatGate,
        conversation_boundary: (
            BetaTelegramConversationBoundary | None
        ) = None,
    ) -> None:
        if start_handler is None:
            raise ValueError(
                "start_handler cannot be None."
            )

        if private_chat_gate is None:
            raise ValueError(
                "private_chat_gate cannot be None."
            )

        self._start_handler = start_handler
        self._private_chat_gate = private_chat_gate
        self._conversation_boundary = conversation_boundary

    # =========================================================
    # Telegram /start
    # =========================================================

    async def handle_start(
        self,
        update: Any,
        context: Any,
    ) -> None:
        user = getattr(
            update,
            "effective_user",
            None,
        )

        chat = getattr(
            update,
            "effective_chat",
            None,
        )

        message = getattr(
            update,
            "effective_message",
            None,
        )

        if user is None or chat is None:
            return

        telegram_user_id = getattr(
            user,
            "id",
            None,
        )

        chat_id = getattr(
            chat,
            "id",
            None,
        )

        chat_type = getattr(
            chat,
            "type",
            None,
        )

        if (
            telegram_user_id is None
            or chat_id is None
        ):
            return

        if chat_type != "private":
            await self._reply(
                message,
                (
                    "Please connect to the "
                    "EasyChatBot Academy from a "
                    "private Telegram chat."
                ),
            )
            return

        token = self._extract_start_token(
            context,
        )

        async def reply(
            text: str,
            user_override: Any = None,
        ) -> None:
            await self._reply(
                message,
                text,
            )

        await self._start_handler.handle(
            token=token,
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            chat_type=chat_type,
            reply=reply,
        )

    # =========================================================
    # Private classroom message flow
    # =========================================================

    async def handle_message(
        self,
        update: Any,
        context: Any = None,
    ) -> str | None:
        """
        Process one Telegram classroom message.

        Response ownership is exclusively inside this adapter.

        Successful flow:

            transport validation
                    |
                    v
            private-chat authorization
                    |
                    v
            conversation boundary
                    |
                    v
              application response
                    |
                    +----> Telegram reply_text()
                    |
                    v
              return response

        The response is delivered exactly once.

        The caller may inspect the returned response but MUST NOT
        send it to Telegram again.
        """

        if self._conversation_boundary is None:
            raise RuntimeError(
                "conversation_boundary is not configured."
            )

        user = getattr(
            update,
            "effective_user",
            None,
        )

        chat = getattr(
            update,
            "effective_chat",
            None,
        )

        message = getattr(
            update,
            "effective_message",
            None,
        )

        if (
            user is None
            or chat is None
            or message is None
        ):
            return None

        telegram_user_id = getattr(
            user,
            "id",
            None,
        )

        chat_type = getattr(
            chat,
            "type",
            None,
        )

        if telegram_user_id is None:
            return None

        # =====================================================
        # HARD TRANSPORT BOUNDARY
        # =====================================================

        if chat_type != "private":
            return None

        # =====================================================
        # MESSAGE VALIDATION
        # =====================================================

        text = getattr(
            message,
            "text",
            None,
        )

        if not isinstance(
            text,
            str,
        ):
            return None

        text = text.strip()

        if not text:
            return None

        # =====================================================
        # BETA ACCESS AUTHORIZATION
        # =====================================================

        try:
            authorized = await (
                self._private_chat_gate.authorize(
                    telegram_user_id=telegram_user_id,
                    chat_type=chat_type,
                )
            )

        except Exception:
            logger.exception(
                "Telegram private-chat authorization failed."
            )

            await self._reply(
                message,
                (
                    "We could not verify your "
                    "EasyChatBot Academy access. "
                    "Please try again."
                ),
            )

            return None

        if not authorized:
            await self._reply(
                message,
                (
                    "Your EasyChatBot Academy Telegram "
                    "access is not authorized and is not "
                    "approved for Beta access."
                ),
            )

            return None

        # =====================================================
        # CONVERSATION BOUNDARY
        # =====================================================

        try:
            response = await (
                self._conversation_boundary.handle_message(
                    telegram_user_id=telegram_user_id,
                    message=text,
                )
            )

        except Exception:
            logger.exception(
                "Telegram classroom conversation processing failed."
            )

            await self._reply(
                message,
                (
                    "Sorry, I could not process "
                    "your classroom message. "
                    "Please try again."
                ),
            )

            return None

        # =====================================================
        # SINGLE RESPONSE DELIVERY POINT
        # =====================================================

        if (
            isinstance(response, str)
            and response.strip()
        ):
            await self._reply(
                message,
                response,
            )

            # Delivery has already happened exactly once.
            #
            # Return only for observability/testing.
            #
            # The runtime MUST ignore this value.
            return response

        return None

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _extract_start_token(
        context: Any,
    ) -> str | None:
        args = getattr(
            context,
            "args",
            None,
        )

        if not args:
            return None

        if not isinstance(
            args,
            (list, tuple),
        ):
            return None

        if not args[0]:
            return None

        return str(
            args[0]
        )

    @staticmethod
    async def _reply(
        message: Any,
        text: str,
    ) -> None:
        if message is None:
            return

        reply_text = getattr(
            message,
            "reply_text",
            None,
        )

        if reply_text is None:
            return

        await reply_text(
            text,
        )


__all__ = [
    "BetaTelegramAdapter",
]
