"""
Hackathon Discovery Notification.

Defines the lightweight user notification produced from a
personalised FlashDealCard.

Architecture:

DiscoveryService
      |
      v
FlashDealCard
      |
      v
DiscoveryNotification
      |
      +--> Telegram
      +--> Web UI
      +--> Future mobile UI

The notification layer is presentation/delivery oriented.

It does not:
- search for products
- access providers
- decide recommendations
- access memory directly
- process payments
- execute purchases
- build a shopping dashboard

The FlashDealCard remains the source of truth for the
discovered offer.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ai_runtime.discovery.flash_deal_card import (
    FlashDealCard,
)


@dataclass(frozen=True)
class DiscoveryNotification:
    """
    Lightweight character-driven notification.

    Designed for a single discovery event rather than a
    persistent shopping dashboard.
    """

    notification_id: str
    user_id: str
    character_id: str
    character_name: str
    title: str
    message: str
    deal: FlashDealCard

    @classmethod
    def from_flash_deal(
        cls,
        *,
        notification_id: str,
        user_id: str,
        deal: FlashDealCard,
    ) -> "DiscoveryNotification":
        """
        Create a notification from an existing FlashDealCard.

        No discovery or commerce logic occurs here.
        """

        if not notification_id.strip():
            raise ValueError(
                "Notification notification_id cannot be empty."
            )

        if not user_id.strip():
            raise ValueError(
                "Notification user_id cannot be empty."
            )

        return cls(
            notification_id=notification_id,
            user_id=user_id,
            character_id=deal.character_id,
            character_name=deal.character_name,
            title=(
                f"{deal.character_name} found something for you"
            ),
            message=deal.character_message,
            deal=deal,
        )

    @property
    def product_name(self) -> str:
        """Return the discovered product name."""

        return self.deal.product_name

    @property
    def relevance_reason(self) -> str:
        """Return the personalisation explanation."""

        return self.deal.relevance_reason

    @property
    def get_deal_url(self) -> str:
        """Return the controlled commerce destination."""

        return self.deal.get_deal_url

    @property
    def more_information_url(self) -> str:
        """Return the vendor information destination."""

        return self.deal.more_information_url

    def render(self) -> str:
        """
        Render a compact notification suitable for a chat UI.

        The full FlashDealCard remains available for the richer
        product presentation.
        """

        discount = (
            self.deal.display_discount
            or "NEW FIND"
        )

        return "\n".join(
            [
                f"{self.character_name}:",
                self.message,
                "",
                f"{discount} — {self.product_name}",
                f"{self.deal.currency} "
                f"{self.deal.current_price:.2f}",
                "",
                "Why this may interest you:",
                self.relevance_reason,
            ]
        )