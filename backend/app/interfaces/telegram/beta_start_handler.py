from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from app.application.services.beta_world_access_service import (
    BetaWorldAccessService,
)
from app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)

logger = logging.getLogger(__name__)


class BetaTelegramStartHandler:
    """
    Application-facing handler for /start <token>.

    Responsibilities:
    - Accept /start only from private Telegram chats.
    - Validate the Beta connection token.
    - Bind the Telegram identity through BetaAccessService.
    - Provision durable access to every catalogue World through
      BetaWorldAccessService.
    - Never select or change the learner's active World from Telegram.
    - Return a successful onboarding response only after World provisioning
      has completed successfully.
    - Use PrivacyIdentifierService for privacy-safe operational logging.

    Architecture:

        Telegram Adapter
            -> BetaTelegramStartHandler
                -> BetaAccessService
                -> BetaWorldAccessService
                    -> WorldAccessService
                        -> LearnerWorldAccess
                -> PrivacyIdentifierService

    Telegram does not access persistence directly and does not select Worlds.
    Raw Telegram or learner identifiers must not be written to logs.
    """

    def __init__(
        self,
        *,
        beta_access_service: BetaAccessService,
        beta_world_access_service: BetaWorldAccessService,
        privacy_identifier_service: PrivacyIdentifierService,
    ) -> None:
        if beta_access_service is None:
            raise ValueError(
                "beta_access_service cannot be None."
            )

        if beta_world_access_service is None:
            raise ValueError(
                "beta_world_access_service cannot be None."
            )

        if privacy_identifier_service is None:
            raise ValueError(
                "privacy_identifier_service cannot be None."
            )

        self._access = beta_access_service
        self._world_access = beta_world_access_service
        self._privacy = privacy_identifier_service

    async def handle(
        self,
        *,
        token: str | None,
        telegram_user_id: int,
        chat_id: int,
        chat_type: str,
        reply: Callable[[str], Any],
    ) -> None:
        """
        Process a Telegram /start <token> request.

        Workflow:

        1. Require a reply callback.
        2. Require a private Telegram chat.
        3. Require a non-empty connection token.
        4. Validate the Beta token and bind the Telegram identity.
        5. Provision durable access to every catalogue World.
        6. Return the success response only after provisioning succeeds.

        Telegram never selects or changes the active World.
        """

        if reply is None:
            raise ValueError(
                "reply callback is required."
            )

        if chat_type != "private":
            await self._send_reply(
                reply,
                (
                    "Please open a private chat with the "
                    "EasyChatBot Academy bot to connect "
                    "your classroom."
                ),
            )
            return

        if not token or not token.strip():
            await self._send_reply(
                reply,
                (
                    "Your classroom connection link is "
                    "missing or invalid."
                ),
            )
            return

        try:
            user = await self._access.validate_and_bind(
                token=token.strip(),
                telegram_id=telegram_user_id,
                chat_id=chat_id,
            )

        except (ValueError, PermissionError) as exc:
            telegram_identifier = (
                self._privacy.pseudonymize_identifier(
                    str(telegram_user_id)
                )
            )

            logger.warning(
                "Telegram Beta binding rejected "
                "telegram_identifier=%s reason=%s",
                telegram_identifier,
                exc,
            )

            await self._send_reply(
                reply,
                str(exc),
            )
            return

        except Exception:
            telegram_identifier = (
                self._privacy.pseudonymize_identifier(
                    str(telegram_user_id)
                )
            )

            logger.exception(
                "Unexpected Telegram Beta binding failure "
                "telegram_identifier=%s",
                telegram_identifier,
            )

            await self._send_reply(
                reply,
                (
                    "We could not connect your Telegram account. "
                    "Please try again or contact EasyChatBot Academy "
                    "support."
                ),
            )
            return

        # W18.3:
        # After the Beta identity has been successfully validated and bound,
        # provision durable access to the complete World catalogue.
        #
        # This does NOT select an active World. World availability and active
        # World selection remain authoritative in the Academy application.
        try:
            await self._world_access.provision_all_worlds(
                beta_user_id=user.user_id,
            )

        except Exception:
            telegram_identifier = (
                self._privacy.pseudonymize_identifier(
                    str(telegram_user_id)
                )
            )
            user_identifier = (
                self._privacy.pseudonymize_identifier(
                    str(user.user_id)
                )
            )

            logger.exception(
                "Telegram Beta World provisioning failed "
                "telegram_identifier=%s user_identifier=%s",
                telegram_identifier,
                user_identifier,
            )

            await self._send_reply(
                reply,
                (
                    "Your Telegram account was connected, but World access "
                    "could not be provisioned successfully. Please try again "
                    "or contact EasyChatBot Academy support."
                ),
            )
            return

        await self._send_reply(
            reply,
            (
                "🌱 Welcome to EasyWorld!\n\n"
                "🎓 Your EasyChatBot classroom is now connected.\n\n"
                "Your available Worlds are managed through "
                "EasyChatBot Academy. Telegram does not select "
                "or change your active World."
            ),
        )

    @staticmethod
    async def _send_reply(
        reply: Callable[[str], Any],
        message: str,
    ) -> None:
        result = reply(message)

        if inspect.isawaitable(result):
            await result


__all__ = [
    "BetaTelegramStartHandler",
]