from __future__ import annotations

import asyncio
import logging
from typing import Any, Protocol
from uuid import UUID

from app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from app.application.beta_access.policies.telegram_policy_messages import (
    TelegramPolicyMessageService,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.private_chat.telegram_private_chat_bridge import (
    TelegramPrivateChatBridge,
)
from app.application.failures.provider_failure import ProviderFailure
from app.application.services.world_access_service import WorldAccessService

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
        private_chat_bridge: TelegramPrivateChatBridge | None = None,
        world_access_service: WorldAccessService | None = None,
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
        if private_chat_bridge is not None and world_access_service is None:
            raise ValueError(
                "world_access_service is required when private_chat_bridge is configured."
            )

        self._private_chat_bridge = private_chat_bridge
        self._world_access_service = world_access_service

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
        # Canonical World authorization for private-chat bridge
        # ---------------------------------------------------------------
        # This check must precede all private-chat lookup/creation and AI
        # side effects. Beta onboarding alone does not grant World access.
        if self._private_chat_bridge is not None:
            raw_user_id = getattr(context, "user_id", None)
            try:
                if isinstance(raw_user_id, UUID):
                    authenticated_user_id = raw_user_id
                elif isinstance(raw_user_id, str) and raw_user_id.strip():
                    authenticated_user_id = UUID(raw_user_id)
                else:
                    raise ValueError("Missing canonical user_id.")

                world_identifier = context.world_id
                if not isinstance(world_identifier, str) or not world_identifier.strip():
                    raise ValueError("Missing canonical world identifier.")
            except (ValueError, TypeError, AttributeError):
                await self._record(
                    event_type="telegram_world_authorization",
                    telegram_user_id=telegram_user_id,
                    outcome="denied",
                    metadata={"reason": "invalid_authoritative_context"},
                )
                return self.UNAUTHORIZED_RESPONSE

            world_access_service = self._world_access_service
            if world_access_service is None:
                # Defense in depth: a missing policy dependency must never
                # permit a bridged private-chat request.
                logger.error(
                    "Telegram World authorization service is not configured."
                )
                return self.SAFE_ERROR_RESPONSE

            try:
                await world_access_service.require_access(
                    user_id=authenticated_user_id,
                    world_identifier=world_identifier,
                )
            except PermissionError:
                await self._record(
                    event_type="telegram_world_authorization",
                    telegram_user_id=telegram_user_id,
                    outcome="denied",
                    metadata={"world_id": world_identifier},
                )
                return self.UNAUTHORIZED_RESPONSE
            except Exception as exc:
                await self._record(
                    event_type="telegram_world_authorization",
                    telegram_user_id=telegram_user_id,
                    outcome="error",
                    metadata={
                        "world_id": world_identifier,
                        "error_type": type(exc).__name__,
                    },
                )
                logger.exception("Telegram World authorization failed.")
                return self.SAFE_ERROR_RESPONSE

            await self._record(
                event_type="telegram_world_authorization",
                telegram_user_id=telegram_user_id,
                outcome="allowed",
                metadata={"world_id": world_identifier},
            )

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
            if self._private_chat_bridge is not None:
                # The canonical context user_id was validated and authorized
                # above; do not derive identity from a non-canonical `user`.
                user_id = str(authenticated_user_id)

                response = await self._private_chat_bridge.handle_message(
                    user_id=str(user_id),
                    world_id=context.world_id,
                    message=clean_message,
                )

            else:
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

        except ProviderFailure as exc:
            await self._record(
                event_type="telegram_classroom_conversation",
                telegram_user_id=telegram_user_id,
                outcome="provider_failure",
                metadata={
                    "world_id": context.world_id,
                    "error_type": type(exc).__name__,
                    "failure_code": exc.code,
                    "provider_id": exc.provider_id,
                },
            )

            logger.warning(
                "Telegram conversation provider failure.",
                extra={
                    "failure_code": exc.code,
                    "provider_id": exc.provider_id,
                },
            )

            raise

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
