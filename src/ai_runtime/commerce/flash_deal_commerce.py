"""
Flash Deal commerce integration boundary.

Converts a user-facing FlashDealCard into explicit commerce
contracts.

Architecture:

FlashDealCard
      |
      v
FlashDealCommerce
      |
      +----> CommerceAction
      |
      +----> PaymentPass
                    |
                    v
             CommerceService
                    |
                    v
             Vendor / Checkout

This module does not:
- process payments
- store payment information
- call vendor APIs
- execute autonomous purchases
- decide whether a product should be recommended

The discovery layer remains responsible for discovery.
The commerce layer remains responsible for commerce.
"""

from __future__ import annotations

from src.ai_runtime.commerce.models import (
    CommerceAction,
    CommerceActionType,
)

from src.ai_runtime.commerce.payment_pass import (
    PaymentPass,
)

from src.ai_runtime.discovery.flash_deal_card import (
    FlashDealCard,
)


class FlashDealCommerce:
    """
    Application boundary between a FlashDealCard and
    the commerce subsystem.
    """

    def create_action(
        self,
        *,
        user_id: str,
        card: FlashDealCard,
    ) -> CommerceAction:
        """
        Create an explicit purchase action from a Flash Deal.

        No purchase occurs here.
        """

        if not user_id.strip():
            raise ValueError(
                "Commerce user_id cannot be empty."
            )

        return CommerceAction(
            user_id=user_id,
            deal_id=card.deal_id,
            action_type=(
                CommerceActionType.INITIATE_PURCHASE
            ),
            destination_url=card.get_deal_url,
            metadata={
                "source": "flash_deal_card",
                "character_id": card.character_id,
                "vendor": card.vendor_name,
            },
        )

    def create_payment_pass(
        self,
        *,
        user_id: str,
        card: FlashDealCard,
        payment_pass_id: str | None = None,
    ) -> PaymentPass:
        """
        Create a demo-only payment handoff from a Flash Deal.

        No payment occurs here.

        The resulting PaymentPass is always:
        - READY
        - DEMO
        - not executed
        """

        if not user_id.strip():
            raise ValueError(
                "Commerce user_id cannot be empty."
            )

        return PaymentPass(
            payment_pass_id=(
                payment_pass_id
                if payment_pass_id is not None
                else f"payment-pass-{card.deal_id}"
            ),
            deal_id=card.deal_id,
            user_id=user_id,
            product_name=card.product_name,
            vendor_name=card.vendor_name,
            amount=card.current_price,
            currency=card.currency,
            checkout_url=card.get_deal_url,
        )