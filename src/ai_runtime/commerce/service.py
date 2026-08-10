"""
Hackathon Commerce Service.

Provides the controlled application boundary for commerce
actions.

The service does not process money itself.

It prepares a commerce action for an approved integration.
"""

from __future__ import annotations

from src.ai_runtime.commerce.models import (
    CommerceAction,
    CommerceActionResult,
    CommerceActionStatus,
)


class CommerceService:
    """
    Controlled commerce application service.

    For the hackathon, the service supports a safe
    external-vendor handoff.

    A future payment/partner adapter can be injected
    without changing DealCard or FlashIdea.
    """

    def initiate(
        self,
        action: CommerceAction,
    ) -> CommerceActionResult:
        """
        Prepare a commerce action.

        For now this establishes the external-vendor
        boundary rather than executing a payment.
        """

        return CommerceActionResult(
            action_id=action.action_id,
            deal_id=action.deal_id,
            status=CommerceActionStatus.REDIRECT,
            next_url=action.destination_url,
            message=(
                "Continue to the approved vendor "
                "to complete the purchase."
            ),
        )