"""
Flash Deal commerce integration boundary.

Converts a user-facing FlashDealCard into an explicit
CommerceAction.

Architecture:

FlashDealCard
      |
      v
FlashDealCommerce
      |
      v
CommerceAction
      |
      v
CommerceService
      |
      v
Approved vendor/payment integration

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