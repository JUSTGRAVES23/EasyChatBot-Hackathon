from __future__ import annotations

import logging
from typing import Any, Protocol

from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from backend.app.application.beta_access.policies.telegram_policy_messages import (
    TelegramPolicyMessageService,
)


logger = logging.getLogger(__name__)


class TelegramPolicy(Protocol):
    async def allow(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
        ...


class TelegramRetryPolicy(TelegramPolicy, Protocol):
    async def retry_after_seconds(
        self,
        *,
        telegram_user_id: int,
    ) -> float:
        ...


class TelegramObservability(Protocol):
    async def record(
        self,
        *,
        event_type: str,
        telegram_user_id: int,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...


class BetaTelegramConversationBoundary:
    """
    Application policy boundary for Beta Telegram conversations.

    Security order:

        Telegram identity
              ↓
        Message validation
              ↓
        Beta authorization
              ↓
        Rate limit
              ↓
        Abuse protection
              ↓
        Conversation service
              ↓
        Observability
              ↓
        Safe response

    Rate limiting and abuse protection deliberately remain
    outside TelegramConversationService and outside Telegram
    transport.

    Learner-facing policy messages are generated from the
    active Learning World language.
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
        rate_limiter: TelegramPolicy | None = None,
        abuse_protector: TelegramPolicy | None = None,
        observability: TelegramObservability | None = None,
        policy_message_service: (
            TelegramPolicyMessageService | None
        ) = None,
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

        self._rate_limiter = rate_limiter

        self._abuse_protector = abuse_protector

        self._observability = observability

        self._policy_message_service = (
            policy_message_service
            or TelegramPolicyMessageService()
        )

    async def _record(
        self,
        *,
        event_type: str,
        telegram_user_id: int,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._observability is None:
            return

        try:
            await self._observability.record(
                event_type=event_type,
                telegram_user_id=telegram_user_id,
                outcome=outcome,
                metadata=metadata,
            )
        except Exception:
            logger.exception(
                "Telegram observability failure "
                "for event_type=%s.",
                event_type,
            )

    async def _retry_after_seconds(
        self,
        policy: TelegramPolicy | None,
        *,
        telegram_user_id: int,
    ) -> float | None:
        if policy is None:
            return None

        method = getattr(
            policy,
            "retry_after_seconds",
            None,
        )

        if method is None:
            return None

        try:
            return await method(
                telegram_user_id=telegram_user_id,
            )
        except Exception as exc:
            await self._record(
                event_type="telegram_classroom_policy",
                telegram_user_id=telegram_user_id,
                outcome="retry_after_error",
                metadata={
                    "error_type": type(exc).__name__,
                },
            )

            return None

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
            await self._record(
                event_type=(
                    "telegram_classroom_authorization"
                ),
                telegram_user_id=telegram_user_id,
                outcome="denied",
            )

            return self.UNAUTHORIZED_RESPONSE

        if self._rate_limiter is not None:
            try:
                allowed = await (
                    self._rate_limiter.allow(
                        telegram_user_id=(
                            telegram_user_id
                        ),
                    )
                )

            except Exception as exc:
                await self._record(
                    event_type=(
                        "telegram_classroom_rate_limit"
                    ),
                    telegram_user_id=telegram_user_id,
                    outcome="error",
                    metadata={
                        "error_type": type(exc).__name__,
                    },
                )

                return self.SAFE_ERROR_RESPONSE

            if not allowed:
                retry_after = (
                    await self._retry_after_seconds(
                        self._rate_limiter,
                        telegram_user_id=(
                            telegram_user_id
                        ),
                    )
                )

                await self._record(
                    event_type=(
                        "telegram_classroom_rate_limit"
                    ),
                    telegram_user_id=telegram_user_id,
                    outcome="blocked",
                    metadata={
                        "world_id": context.world_id,
                    },
                )

                return (
                    self._policy_message_service
                    .rate_limit_message(
                        context=context,
                        retry_after_seconds=(
                            retry_after
                        ),
                    )
                )

        if self._abuse_protector is not None:
            try:
                allowed = await (
                    self._abuse_protector.allow(
                        telegram_user_id=(
                            telegram_user_id
                        ),
                    )
                )

            except Exception as exc:
                await self._record(
                    event_type=(
                        "telegram_classroom_abuse_protection"
                    ),
                    telegram_user_id=telegram_user_id,
                    outcome="error",
                    metadata={
                        "error_type": type(exc).__name__,
                    },
                )

                return self.SAFE_ERROR_RESPONSE

            if not allowed:
                retry_after = (
                    await self._retry_after_seconds(
                        self._abuse_protector,
                        telegram_user_id=(
                            telegram_user_id
                        ),
                    )
                )

                await self._record(
                    event_type=(
                        "telegram_classroom_abuse_protection"
                    ),
                    telegram_user_id=telegram_user_id,
                    outcome="blocked",
                    metadata={
                        "world_id": context.world_id,
                    },
                )

                return (
                    self._policy_message_service
                    .abuse_limit_message(
                        context=context,
                        retry_after_seconds=(
                            retry_after
                        ),
                    )
                )

        await self._record(
            event_type="telegram_classroom_message",
            telegram_user_id=telegram_user_id,
            outcome="accepted",
            metadata={
                "world_id": context.world_id,
                "character": context.character,
                "level": context.level,
            },
        )

        try:
            context_handler = getattr(
                self._conversation_service,
                "handle_telegram_message_with_context",
                None,
            )

            if context_handler is not None:
                response = await context_handler(
                    telegram_user_id=telegram_user_id,
                    message=clean_message,
                    context=context,
                )

            else:
                response = await (
                    self._conversation_service
                    .handle_telegram_message(
                        telegram_user_id=telegram_user_id,
                        message=clean_message,
                    )
                )

        except Exception as exc:
            await self._record(
                event_type=(
                    "telegram_classroom_conversation"
                ),
                telegram_user_id=telegram_user_id,
                outcome="error",
                metadata={
                    "error_type": type(exc).__name__,
                },
            )

            logger.exception(
                "Telegram conversation processing failed."
            )

            return self.SAFE_ERROR_RESPONSE

        await self._record(
            event_type=(
                "telegram_classroom_conversation"
            ),
            telegram_user_id=telegram_user_id,
            outcome="success",
            metadata={
                "world_id": context.world_id,
                "character": context.character,
                "level": context.level,
            },
        )

        return response

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

        if len(clean_message) > (
            cls.MAX_TELEGRAM_MESSAGE_LENGTH
        ):
            raise ValueError(
                "Telegram message is too long. "
                "Maximum length is "
                f"{cls.MAX_TELEGRAM_MESSAGE_LENGTH} "
                "characters."
            )

        return clean_message


__all__ = [
    "BetaTelegramConversationBoundary",
]