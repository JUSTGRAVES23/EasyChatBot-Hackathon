"""Application handler for Telegram Beta onboarding via /start.

W18.3 Telegram Provisioning
----------------------------
This handler is the application boundary for Telegram Beta onboarding.

Responsibilities:
- Validate the Telegram connection token.
- Bind the Telegram identity to the eligible Beta account.
- Provision durable access to all catalogue Worlds.
- Never select or change the user's active World.
- Return success only after provisioning has completed successfully.

Architecture:
    Telegram Adapter
        -> BetaTelegramStartHandler
            -> BetaAccessService
            -> BetaWorldAccessService
                -> WorldAccessService
                    -> LearnerWorldAccess

The handler does not access persistence directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.application.services.beta_access_service import BetaAccessService
from app.application.services.beta_world_access_service import (
    BetaWorldAccessService,
)


class TelegramStartResponsePort(Protocol):
    """Port used by the start handler to send Telegram responses."""

    async def send_message(
        self,
        telegram_id: int,
        text: str,
    ) -> None:
        """Send a response message to the Telegram user."""
        ...


@dataclass(frozen=True)
class BetaTelegramStartResult:
    """Result of processing a Telegram /start command."""

    success: bool
    message: str


class BetaTelegramStartHandler:
    """Handle Telegram /start <token> Beta onboarding.

    The handler deliberately keeps Telegram transport concerns outside the
    application service. The Telegram adapter is responsible for extracting
    the token and Telegram identity; this handler is responsible for the
    application workflow.

    W18.3 provisioning occurs only after the Beta connection token has been
    successfully validated and the Telegram identity has been bound.

    Telegram never selects or changes the active Learning World. Provisioning
    only grants durable access to the complete catalogue portfolio.
    """

    def __init__(
        self,
        beta_access_service: BetaAccessService,
        beta_world_access_service: BetaWorldAccessService,
    ) -> None:
        self._beta_access_service = beta_access_service
        self._beta_world_access_service = beta_world_access_service

    async def handle(
        self,
        *,
        telegram_id: int,
        token: str,
        response_port: TelegramStartResponsePort,
    ) -> BetaTelegramStartResult:
        """Process a Telegram /start <token> request.

        Workflow:
        1. Validate the Beta connection token.
        2. Validate Beta eligibility through BetaAccessService.
        3. Bind the Telegram identity.
        4. Provision durable access to every catalogue World.
        5. Send the success response only after provisioning succeeds.

        Provisioning failures are intentionally not converted into a
        successful onboarding response. This prevents the Telegram user from
        being told that onboarding succeeded when the required World access
        provisioning did not complete.
        """

        if not token or not token.strip():
            message = (
                "This Telegram connection link is invalid. "
                "Please request a new connection link from EasyChatBot Academy."
            )

            await response_port.send_message(
                telegram_id,
                message,
            )

            return BetaTelegramStartResult(
                success=False,
                message=message,
            )

        try:
            user = await self._beta_access_service.validate_and_bind(
                token=token.strip(),
                telegram_id=telegram_id,
            )

        except Exception:
            message = (
                "We could not connect your Telegram account. "
                "The connection link may be invalid, expired, or no longer "
                "available. Please request a new connection link from "
                "EasyChatBot Academy."
            )

            await response_port.send_message(
                telegram_id,
                message,
            )

            return BetaTelegramStartResult(
                success=False,
                message=message,
            )

        try:
            await self._beta_world_access_service.provision_all_worlds(
                beta_user_id=user.user_id,
            )

        except Exception:
            message = (
                "Your Telegram account was connected, but World access could "
                "not be provisioned successfully. Please try connecting again "
                "or contact EasyChatBot Academy support."
            )

            await response_port.send_message(
                telegram_id,
                message,
            )

            return BetaTelegramStartResult(
                success=False,
                message=message,
            )

        message = (
            "Your Telegram account has been connected successfully. "
            "Your available Worlds are managed through EasyChatBot Academy. "
            "Telegram does not select or change your active World."
        )

        await response_port.send_message(
            telegram_id,
            message,
        )

        return BetaTelegramStartResult(
            success=True,
            message=message,
        )