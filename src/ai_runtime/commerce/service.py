"""
Hackathon Commerce Service.

Provides the controlled application boundary for commerce
actions and demo-only payment handoffs.

The service does not process money itself.

It prepares commerce actions and payment handoffs for an
approved integration.
"""

from __future__ import annotations

from src.ai_runtime.commerce.models import (
    CommerceAction,
    CommerceActionResult,
    CommerceActionStatus,
)

from src.ai_runtime.commerce.payment_pass import (
    PaymentPass,
)


class CommerceService:
    """
    Controlled commerce application service.

    For the hackathon, the service supports:
    - safe external-vendor handoff
    - demo-only payment preparation

    A future payment/partner adapter can be injected without
    changing DealCard or FlashDeal.
    """

    def initiate(
        self,
        action: CommerceAction,
    ) -> CommerceActionResult:
        """
        Prepare a commerce action.

        This establishes the external-vendor boundary rather
        than executing a payment.
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

    def prepare_payment(
        self,
        payment_pass: PaymentPass,
    ) -> PaymentPass:
        """
        Prepare a demo-only payment handoff.

        No payment provider is called and no transaction is
        executed. The PaymentPass contract itself enforces
        READY + DEMO semantics.
        """

        if not payment_pass.is_ready:
            raise ValueError(
                "PaymentPass must be READY."
            )

        if not payment_pass.is_demo_only:
            raise ValueError(
                "Hackathon payment must use DEMO execution mode."
            )

        return payment_pass