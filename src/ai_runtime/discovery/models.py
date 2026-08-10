"""
Hackathon Discovery domain models.

These models represent the small discovery layer required
for the hackathon experience.

The hackathon is NOT a marketplace.

EasyChatBot:
    discovers products
    evaluates opportunities
    presents character-led flash ideas
    provides an outbound vendor link

The external vendor:
    owns the product page
    owns checkout
    owns payment
    fulfils the purchase

Architecture:

Discovery Intelligence
        |
        v
     DealCard
        |
        +--> CommerceLink
        |
        v
    FlashIdea
        |
        v
     Character
        |
        v
       User
        |
        v
 External Vendor
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class CommerceLinkType(str, Enum):
    """
    Type of outbound commerce link.
    """

    DIRECT = "direct"

    AFFILIATE = "affiliate"


@dataclass(frozen=True)
class CommerceLink:
    """
    Outbound link to the external vendor.

    EasyChatBot does not process the transaction.

    The destination remains the vendor's website.
    """

    vendor: str

    destination_url: str

    link_type: CommerceLinkType = (
        CommerceLinkType.DIRECT
    )

    tracking_url: str | None = None

    def __post_init__(self) -> None:
        """
        Validate the commerce link.
        """

        if not self.vendor.strip():
            raise ValueError(
                "Commerce vendor cannot be empty."
            )

        if not self.destination_url.strip():
            raise ValueError(
                "Commerce destination URL "
                "cannot be empty."
            )

        if not (
            self.destination_url.startswith(
                "https://"
            )
            or self.destination_url.startswith(
                "http://"
            )
        ):
            raise ValueError(
                "Commerce destination URL must "
                "use HTTP or HTTPS."
            )

        if self.tracking_url is not None:
            if not self.tracking_url.strip():
                raise ValueError(
                    "Commerce tracking URL cannot "
                    "be empty when provided."
                )

            if not (
                self.tracking_url.startswith(
                    "https://"
                )
                or self.tracking_url.startswith(
                    "http://"
                )
            ):
                raise ValueError(
                    "Commerce tracking URL must "
                    "use HTTP or HTTPS."
                )

    @property
    def click_url(self) -> str:
        """
        Return the URL that should be opened by the user.

        A tracking URL takes precedence when one is
        available.
        """

        return (
            self.tracking_url
            if self.tracking_url is not None
            else self.destination_url
        )


@dataclass(frozen=True)
class DealCard:
    """
    Compact representation of a discovered product opportunity.

    This is intentionally not a product catalogue entity.

    It represents a single discovery opportunity surfaced
    to a user.
    """

    product_name: str

    vendor: str

    price: float

    currency: str

    commerce_link: CommerceLink

    deal_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    previous_price: float | None = None

    discount_percentage: float | None = None

    source: str | None = None

    description: str | None = None

    discovered_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Validate the DealCard.
        """

        if not self.product_name.strip():
            raise ValueError(
                "Deal product name cannot be empty."
            )

        if not self.vendor.strip():
            raise ValueError(
                "Deal vendor cannot be empty."
            )

        if self.price < 0:
            raise ValueError(
                "Deal price cannot be negative."
            )

        if not self.currency.strip():
            raise ValueError(
                "Deal currency cannot be empty."
            )

        if (
            self.previous_price is not None
            and self.previous_price < 0
        ):
            raise ValueError(
                "Deal previous price cannot "
                "be negative."
            )

        if (
            self.discount_percentage is not None
            and not 0 <= self.discount_percentage <= 100
        ):
            raise ValueError(
                "Deal discount percentage must "
                "be between 0 and 100."
            )

        if (
            self.commerce_link.vendor
            != self.vendor
        ):
            raise ValueError(
                "Deal vendor must match the "
                "commerce link vendor."
            )


@dataclass(frozen=True)
class FlashIdea:
    """
    Character-led presentation of a discovered deal.

    A FlashIdea is the user-facing discovery message.

    It is not a transaction.
    """

    character_id: str

    deal_id: str

    message: str

    title: str = "Flash idea"

    idea_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Validate the FlashIdea.
        """

        if not self.character_id.strip():
            raise ValueError(
                "FlashIdea character_id "
                "cannot be empty."
            )

        if not self.deal_id.strip():
            raise ValueError(
                "FlashIdea deal_id "
                "cannot be empty."
            )

        if not self.message.strip():
            raise ValueError(
                "FlashIdea message "
                "cannot be empty."
            )