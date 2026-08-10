"""
Hackathon Flash Deal Card presentation contract.

This module defines the user-facing data contract for the
EasyChatBot Flash Deal Card shown by a character.

Architecture:

Parallel / Discovery
        |
        v
     DealCard
        |
        +---- Memory Context
        |
        +---- Character
        |
        v
  FlashDealCard
        |
        +---- GET DEAL
        |
        +---- MORE INFORMATION
        |
        v
 External Vendor / Future Commerce Flow

The model is presentation-oriented.

It does not:
- call providers
- access SQLite
- perform payments
- execute agents
- scrape vendor pages
- invent product information
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.ai_runtime.discovery.models import DealCard


@dataclass(frozen=True)
class FlashDealCard:
    """
    User-facing Flash Deal Card.

    This contract maps directly to the hackathon UX:

    - character discovery
    - product information
    - pricing
    - discount
    - personal relevance
    - vendor
    - GET DEAL action
    - MORE INFORMATION action

    The card deliberately contains no payment implementation.
    """

    deal_id: str
    character_id: str
    character_name: str
    character_message: str

    product_name: str
    product_image_url: str
    tagline: str
    highlights: tuple[str, ...]

    current_price: float
    currency: str
    previous_price: float | None
    discount_percentage: float | None
    savings: float | None

    relevance_reason: str

    vendor_name: str
    more_information_url: str
    get_deal_url: str

    badge: str = "NEW FIND!"
    card_id: str | None = None
    metadata: dict[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Validate the presentation contract.
        """

        required_text_fields = {
            "deal_id": self.deal_id,
            "character_id": self.character_id,
            "character_name": self.character_name,
            "character_message": self.character_message,
            "product_name": self.product_name,
            "product_image_url": self.product_image_url,
            "tagline": self.tagline,
            "currency": self.currency,
            "relevance_reason": self.relevance_reason,
            "vendor_name": self.vendor_name,
            "more_information_url": self.more_information_url,
            "get_deal_url": self.get_deal_url,
        }

        for field_name, value in required_text_fields.items():
            if not value.strip():
                raise ValueError(
                    f"FlashDealCard {field_name} cannot be empty."
                )

        if not self.highlights:
            raise ValueError(
                "FlashDealCard must contain at least one highlight."
            )

        if any(
            not highlight.strip()
            for highlight in self.highlights
        ):
            raise ValueError(
                "FlashDealCard highlights cannot contain empty values."
            )

        if self.current_price < 0:
            raise ValueError(
                "FlashDealCard current_price cannot be negative."
            )

        if (
            self.previous_price is not None
            and self.previous_price < 0
        ):
            raise ValueError(
                "FlashDealCard previous_price cannot be negative."
            )

        if (
            self.discount_percentage is not None
            and not 0 <= self.discount_percentage <= 100
        ):
            raise ValueError(
                "FlashDealCard discount_percentage must be "
                "between 0 and 100."
            )

        if self.savings is not None and self.savings < 0:
            raise ValueError(
                "FlashDealCard savings cannot be negative."
            )

        self._validate_url(
            self.product_image_url,
            "product_image_url",
        )
        self._validate_url(
            self.more_information_url,
            "more_information_url",
        )
        self._validate_url(
            self.get_deal_url,
            "get_deal_url",
        )

    @staticmethod
    def _validate_url(
        url: str,
        field_name: str,
    ) -> None:
        """
        Validate a user-facing URL.
        """

        if not (
            url.startswith("https://")
            or url.startswith("http://")
        ):
            raise ValueError(
                f"FlashDealCard {field_name} must use "
                "HTTP or HTTPS."
            )

    @classmethod
    def from_deal(
        cls,
        *,
        deal: DealCard,
        character_id: str,
        character_name: str,
        character_message: str,
        relevance_reason: str,
        product_image_url: str,
        tagline: str,
        highlights: list[str] | tuple[str, ...],
        badge: str = "NEW FIND!",
        metadata: dict[str, str] | None = None,
    ) -> "FlashDealCard":
        """
        Build a presentation card from a domain DealCard.

        Product, pricing and vendor information comes from the
        DealCard. Character and personalisation information is
        supplied explicitly by the application layer.

        No product or pricing information is invented here.
        """

        savings: float | None = None

        if (
            deal.previous_price is not None
            and deal.previous_price > deal.price
        ):
            savings = round(
                deal.previous_price - deal.price,
                2,
            )

        return cls(
            deal_id=deal.deal_id,
            character_id=character_id,
            character_name=character_name,
            character_message=character_message,
            product_name=deal.product_name,
            product_image_url=product_image_url,
            tagline=tagline,
            highlights=tuple(highlights),
            current_price=deal.price,
            currency=deal.currency,
            previous_price=deal.previous_price,
            discount_percentage=deal.discount_percentage,
            savings=savings,
            relevance_reason=relevance_reason,
            vendor_name=deal.vendor,
            more_information_url=(
                deal.commerce_link.destination_url
            ),
            get_deal_url=(
                deal.commerce_link.click_url
            ),
            badge=badge,
            metadata=(
                dict(metadata)
                if metadata is not None
                else {}
            ),
        )

    @property
    def has_discount(self) -> bool:
        """Return whether a verified discount exists."""

        return (
            self.discount_percentage is not None
            and self.discount_percentage > 0
        )

    @property
    def has_previous_price(self) -> bool:
        """Return whether a previous price is available."""

        return self.previous_price is not None

    @property
    def display_discount(self) -> str | None:
        """Return a UI-friendly discount label."""

        if self.discount_percentage is None:
            return None

        return f"{self.discount_percentage:.0f}% OFF"

    @property
    def display_savings(self) -> str | None:
        """Return a UI-friendly savings label."""

        if self.savings is None:
            return None

        return f"Save {self.currency} {self.savings:.2f}"