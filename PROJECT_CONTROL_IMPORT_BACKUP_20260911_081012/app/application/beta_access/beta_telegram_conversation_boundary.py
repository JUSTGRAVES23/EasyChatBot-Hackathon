from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol

from app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from app.application.beta_access.policies.telegram_policy_messages import (
    TelegramPolicyMessageService,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)

logger = logging.getLogger(__name__)


class TelegramPolicy(Protocol):
    async def allow(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
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
    """Application policy boundary for Beta Telegram conversations."""

    MAX_TELEGRAM_MESSAGE_LENGTH = 4096

    TELEGRAM_FUNCTIONALITY_ID = "telegram"
    TELEGRAM_OPERATIONS_ENVIRONMENT = "adults"

    SAFE_ERROR_RESPONSE = (
        "Sorry, something went wrong while processing your message. "
        "Please try again later."
    )

    UNAUTHORIZED_RESPONSE = (
        "Sorry, this Telegram account is not authorized "
        "and is not approved for Beta access."
    )

    FUNCTIONALITY_DISABLED_RESPONSE = (
        "Sorry, the Telegram classroom is temporarily unavailable. "
        "Please try again later."
    )

    def __init__(
        self,
        *,
        conversation_service: Any,
        beta_access_service: BetaAccessService,
        rate_limiter: TelegramPolicy | None = None,
        abuse_protector: TelegramPolicy | None = None,
        observability: TelegramObservability | None = None,
        policy_message_service: TelegramPolicyMessageService | None = None,
        functionality_control_service: (
            FunctionalityOperationalControlService | None
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

        self._conversation_service = conversation_service
        self._beta_access_service = beta_access_service
        self._rate_limiter = rate_limiter
        self._abuse_protector = abuse_protector
        self._observability = observability
        self._policy_message_service = (
            policy_message_service
            or TelegramPolicyMessageService()
        )
        self._functionality_control_service = (
            functionality_control_service
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
                "Telegram observability failure for event_type=%s.",
                event_type,
            )

    async def _functionality_is_enabled(
        self,
        *,
        telegram_user_id: int,
    ) -> bool:
        control_service = self._functionality_control_service

        # Legacy/unit-test compositions may omit operational control.
        # Production composition always supplies it.
        if control_service is None:
            return True

        environment = self.TELEGRAM_OPERATIONS_ENVIRONMENT
        environment_value = getattr(
            environment,
            "value",
            environment,
        )

        try:
            availability = await asyncio.to_thread(
                control_service.get_availability,
                environment=environment,
                functionality_id=self.TELEGRAM_FUNCTIONALITY_ID,
            )

        except Exception as exc:
            await self._record(
                event_type="telegram_classroom_functionality_control",
                telegram_user_id=telegram_user_id,
                outcome="error",
                metadata={
                    "functionality_id": self.TELEGRAM_FUNCTIONALITY_ID,
                    "environment": environment_value,
                    "error_type": type(exc).__name__,
                },
            )

            logger.exception(
                "Telegram functionality-control lookup failed."
            )

            # Fail closed: an unavailable control plane must not
            # permit Telegram classroom processing.
            return False

        enabled = availability == "enabled"

        await self._record(
            event_type="telegram_classroom_functionality_control",
            telegram_user_id=telegram_user_id,
            outcome="allowed" if enabled else "blocked",
            metadata={
                "functionality_id": self.TELEGRAM_FUNCTIONALITY_ID,
                "environment": environment_value,
            },
        )

        return enabled

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

        # ---------------------------------------------------------------
        # Beta authorization / World context
        # ---------------------------------------------------------------
        try:
            context = await (
                self._beta_access_service
                .get_conversation_context(
                    telegram_user_id,
                )
            )

        except PermissionError:
            await self._record(
                event_type="telegram_classroom_authorization",
                telegram_user_id=telegram_user_id,
                outcome="denied",
            )

            return self.UNAUTHORIZED_RESPONSE

        except Exception as exc:
            await self._record(
                event_type="telegram_classroom_authorization",
                telegram_user_id=telegram_user_id,
                outcome="error",
                metadata={
                    "error_type": type(exc).__name__,
                },
            )

            logger.exception(
                "Telegram Beta access/context resolution failed."
            )

            return self.SAFE_ERROR_RESPONSE

        # ---------------------------------------------------------------
        # Functionality operational control
        # ---------------------------------------------------------------
        #
        # This deliberately occurs after authorization/context resolution
        # but before rate limiting, abuse protection, persistence or AI.
        #
        if not await self._functionality_is_enabled(
            telegram_user_id=telegram_user_id,
        ):
            return self.FUNCTIONALITY_DISABLED_RESPONSE

        # ---------------------------------------------------------------
        # Rate limiting
        # ---------------------------------------------------------------
        if self._rate_limiter is not None:
            try:
                allowed = await self._rate_limiter.allow(
                    telegram_user_id=telegram_user_id,
                )

            except Exception as exc:
                await self._record(
                    event_type="telegram_classroom_rate_limit",
                    telegram_user_id=telegram_user_id,
                    outcome="error",
                    metadata={
                        "error_type": type(exc).__name__,
                    },
                )

                logger.exception(
                    "Telegram rate limiter failed."
                )

                return self.SAFE_ERROR_RESPONSE

            if not allowed:
                await self._record(
                    event_type="telegram_classroom_rate_limit",
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
                            self._get_rate_limit_retry_after_seconds()
                        ),
                    )
                )

        # ---------------------------------------------------------------
        # Abuse protection
        # ---------------------------------------------------------------
        if self._abuse_protector is not None:
            try:
                allowed = await self._abuse_protector.allow(
                    telegram_user_id=telegram_user_id,
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

                logger.exception(
                    "Telegram abuse protection failed."
                )

                return self.SAFE_ERROR_RESPONSE

            if not allowed:
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
                    .abuse_protection_message(
                        context=context,
                        retry_after_seconds=(
                            self._get_abuse_retry_after_seconds()
                        ),
                    )
                )

        # ---------------------------------------------------------------
        # Accepted classroom message
        # ---------------------------------------------------------------
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

        # ---------------------------------------------------------------
        # Conversation / AI Runtime
        # ---------------------------------------------------------------
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
                event_type="telegram_classroom_conversation",
                telegram_user_id=telegram_user_id,
                outcome="error",
                metadata={
                    "world_id": context.world_id,
                    "error_type": type(exc).__name__,
                },
            )

            logger.exception(
                "Telegram conversation processing failed."
            )

            return self.SAFE_ERROR_RESPONSE

        # ---------------------------------------------------------------
        # Successful completion
        # ---------------------------------------------------------------
        await self._record(
            event_type="telegram_classroom_conversation",
            telegram_user_id=telegram_user_id,
            outcome="success",
            metadata={
                "world_id": context.world_id,
                "character": context.character,
                "level": context.level,
            },
        )

        return response

    def _get_rate_limit_retry_after_seconds(self) -> int:
        limiter = self._rate_limiter

        if limiter is None:
            return 60

        window = getattr(
            limiter,
            "window_seconds",
            60,
        )

        try:
            return max(
                1,
                int(float(window)),
            )
        except (TypeError, ValueError):
            return 60

    def _get_abuse_retry_after_seconds(self) -> int:
        protector = self._abuse_protector

        if protector is None:
            return 60

        window = getattr(
            protector,
            "window_seconds",
            60,
        )

        try:
            return max(
                1,
                int(float(window)),
            )
        except (TypeError, ValueError):
            return 60

    @classmethod
    def _validate_telegram_user_id(
        cls,
        telegram_user_id: int,
    ) -> None:
        if isinstance(telegram_user_id, bool):
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

        if len(clean_message) > cls.MAX_TELEGRAM_MESSAGE_LENGTH:
            raise ValueError(
                "Telegram message is too long. Maximum length is "
                f"{cls.MAX_TELEGRAM_MESSAGE_LENGTH} characters."
            )

        return clean_message


__all__ = [
    "BetaTelegramConversationBoundary",
]


