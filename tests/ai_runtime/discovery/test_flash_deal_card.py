"""
Tests for the hackathon Flash Deal Card presentation contract.

The tests validate the user-facing card described by the
hackathon UX:

Character
    ↓
Product
    ↓
Pricing / Deal
    ↓
Why relevant to you
    ↓
Vendor
    ↓
GET DEAL / MORE INFORMATION
"""

import pytest

from src.ai_runtime.discovery.flash_deal_card import (
    FlashDealCard,
)

from src.ai_runtime.discovery.models import (
    CommerceLink,
    CommerceLinkType,
    DealCard,
)


def make_deal(
    *,
    affiliate: bool = False,
) -> DealCard:
    link = CommerceLink(
        vendor="eBay",
        destination_url=(
            "https://www.ebay.com/itm/example"
        ),
        link_type=(
            CommerceLinkType.AFFILIATE
            if affiliate
            else CommerceLinkType.DIRECT
        ),
        tracking_url=(
            "https://tracking.example.com/deal/001"
            if affiliate
            else None
        ),
    )

    return DealCard(
        product_name="iPhone 17 Pro",
        vendor="eBay",
        price=999.99,
        currency="EUR",
        previous_price=1199.00,
        discount_percentage=17.0,
        commerce_link=link,
        source="parallel",
        description="Pro smartphone with advanced camera system.",
    )


def test_flash_deal_card_is_created_from_deal():

    deal = make_deal()

    card = FlashDealCard.from_deal(
        deal=deal,
        character_id="yeti",
        character_name="Yeti",
        character_message="Look what I found!",
        relevance_reason=(
            "This matches your interest in powerful "
            "mobile photography."
        ),
        product_image_url=(
            "https://example.com/images/iphone17.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=[
            "Pro camera system",
            "A19 Bionic chip",
            "All-day battery life",
            "6.3-inch Super Retina XDR display",
        ],
    )

    assert card.deal_id == deal.deal_id
    assert card.character_id == "yeti"
    assert card.character_name == "Yeti"

    assert card.product_name == "iPhone 17 Pro"
    assert card.tagline == "Pro. Beautiful. Powerful."

    assert len(card.highlights) == 4

    assert card.current_price == 999.99
    assert card.previous_price == 1199.00
    assert card.discount_percentage == 17.0

    assert card.savings == 199.01

    assert card.vendor_name == "eBay"

    assert (
        card.more_information_url
        == "https://www.ebay.com/itm/example"
    )

    assert (
        card.get_deal_url
        == "https://www.ebay.com/itm/example"
    )


def test_flash_deal_card_contains_personal_relevance():

    deal = make_deal()

    card = FlashDealCard.from_deal(
        deal=deal,
        character_id="yeti",
        character_name="Yeti",
        character_message="Look what I found!",
        relevance_reason=(
            "You often look for strong mobile "
            "photography performance."
        ),
        product_image_url=(
            "https://example.com/images/iphone17.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=[
            "Pro camera system",
        ],
    )

    assert (
        card.relevance_reason
        == "You often look for strong mobile "
        "photography performance."
    )


def test_flash_deal_card_exposes_discount():

    deal = make_deal()

    card = FlashDealCard.from_deal(
        deal=deal,
        character_id="yeti",
        character_name="Yeti",
        character_message="Look what I found!",
        relevance_reason="Relevant to you.",
        product_image_url=(
            "https://example.com/images/iphone17.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=["Pro camera system"],
    )

    assert card.has_discount is True
    assert card.has_previous_price is True

    assert card.display_discount == "17% OFF"
    assert card.display_savings == "Save EUR 199.01"


def test_flash_deal_card_uses_affiliate_click_url():

    deal = make_deal(
        affiliate=True
    )

    card = FlashDealCard.from_deal(
        deal=deal,
        character_id="yeti",
        character_name="Yeti",
        character_message="Look what I found!",
        relevance_reason="Relevant to you.",
        product_image_url=(
            "https://example.com/images/iphone17.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=["Pro camera system"],
    )

    assert (
        card.more_information_url
        == "https://www.ebay.com/itm/example"
    )

    assert (
        card.get_deal_url
        == "https://tracking.example.com/deal/001"
    )


def test_flash_deal_card_requires_product_image_url():

    with pytest.raises(
        ValueError,
        match="product_image_url cannot be empty",
    ):
        FlashDealCard(
            deal_id="deal-001",
            character_id="yeti",
            character_name="Yeti",
            character_message="Look what I found!",
            product_name="iPhone 17 Pro",
            product_image_url="",
            tagline="Pro. Beautiful. Powerful.",
            highlights=("Pro camera system",),
            current_price=999.99,
            currency="EUR",
            previous_price=1199.00,
            discount_percentage=17.0,
            savings=199.01,
            relevance_reason="Relevant to you.",
            vendor_name="eBay",
            more_information_url=(
                "https://www.ebay.com/itm/example"
            ),
            get_deal_url=(
                "https://www.ebay.com/itm/example"
            ),
        )


def test_flash_deal_card_rejects_invalid_image_url():

    with pytest.raises(
        ValueError,
        match="product_image_url must use HTTP or HTTPS",
    ):
        FlashDealCard(
            deal_id="deal-001",
            character_id="yeti",
            character_name="Yeti",
            character_message="Look what I found!",
            product_name="iPhone 17 Pro",
            product_image_url="invalid-image-url",
            tagline="Pro. Beautiful. Powerful.",
            highlights=("Pro camera system",),
            current_price=999.99,
            currency="EUR",
            previous_price=1199.00,
            discount_percentage=17.0,
            savings=199.01,
            relevance_reason="Relevant to you.",
            vendor_name="eBay",
            more_information_url=(
                "https://www.ebay.com/itm/example"
            ),
            get_deal_url=(
                "https://www.ebay.com/itm/example"
            ),
        )


def test_flash_deal_card_rejects_empty_highlights():

    with pytest.raises(
        ValueError,
        match="at least one highlight",
    ):
        FlashDealCard(
            deal_id="deal-001",
            character_id="yeti",
            character_name="Yeti",
            character_message="Look what I found!",
            product_name="iPhone 17 Pro",
            product_image_url=(
                "https://example.com/images/iphone17.jpg"
            ),
            tagline="Pro. Beautiful. Powerful.",
            highlights=(),
            current_price=999.99,
            currency="EUR",
            previous_price=1199.00,
            discount_percentage=17.0,
            savings=199.01,
            relevance_reason="Relevant to you.",
            vendor_name="eBay",
            more_information_url=(
                "https://www.ebay.com/itm/example"
            ),
            get_deal_url=(
                "https://www.ebay.com/itm/example"
            ),
        )


def test_flash_deal_card_rejects_invalid_discount():

    with pytest.raises(
        ValueError,
        match="discount_percentage must be between 0 and 100",
    ):
        FlashDealCard(
            deal_id="deal-001",
            character_id="yeti",
            character_name="Yeti",
            character_message="Look what I found!",
            product_name="iPhone 17 Pro",
            product_image_url=(
                "https://example.com/images/iphone17.jpg"
            ),
            tagline="Pro. Beautiful. Powerful.",
            highlights=("Pro camera system",),
            current_price=999.99,
            currency="EUR",
            previous_price=1199.00,
            discount_percentage=120.0,
            savings=199.01,
            relevance_reason="Relevant to you.",
            vendor_name="eBay",
            more_information_url=(
                "https://www.ebay.com/itm/example"
            ),
            get_deal_url=(
                "https://www.ebay.com/itm/example"
            ),
        )


def test_flash_deal_card_allows_no_discount():

    deal = DealCard(
        product_name="Travel Backpack",
        vendor="Example Vendor",
        price=89.00,
        currency="EUR",
        commerce_link=CommerceLink(
            vendor="Example Vendor",
            destination_url=(
                "https://example.com/backpack"
            ),
        ),
    )

    card = FlashDealCard.from_deal(
        deal=deal,
        character_id="yeti",
        character_name="Yeti",
        character_message="I found something for you.",
        relevance_reason="This matches your travel interests.",
        product_image_url=(
            "https://example.com/images/backpack.jpg"
        ),
        tagline="Lightweight and practical.",
        highlights=[
            "Lightweight",
            "Water resistant",
        ],
    )

    assert card.has_discount is False
    assert card.has_previous_price is False
    assert card.display_discount is None
    assert card.display_savings is None
    assert card.savings is None