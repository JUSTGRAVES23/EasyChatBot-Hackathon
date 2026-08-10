"""
Tests for the hackathon Discovery domain models.
"""

import pytest

from src.ai_runtime.discovery.models import (
    CommerceLink,
    CommerceLinkType,
    DealCard,
    FlashIdea,
)


def test_commerce_link_uses_vendor_destination():

    link = CommerceLink(
        vendor="Example Vendor",
        destination_url=(
            "https://example.com/product/123"
        ),
    )

    assert link.vendor == "Example Vendor"

    assert (
        link.destination_url
        == "https://example.com/product/123"
    )

    assert (
        link.link_type
        == CommerceLinkType.DIRECT
    )

    assert (
        link.click_url
        == link.destination_url
    )


def test_commerce_link_supports_affiliate_url():

    link = CommerceLink(
        vendor="Example Vendor",
        destination_url=(
            "https://example.com/product/123"
        ),
        link_type=CommerceLinkType.AFFILIATE,
        tracking_url=(
            "https://example.com/track/123"
        ),
    )

    assert (
        link.link_type
        == CommerceLinkType.AFFILIATE
    )

    assert (
        link.click_url
        == "https://example.com/track/123"
    )


def test_commerce_link_rejects_invalid_url():

    with pytest.raises(
        ValueError,
        match="HTTP or HTTPS",
    ):
        CommerceLink(
            vendor="Example Vendor",
            destination_url="not-a-url",
        )


def test_deal_card_contains_external_vendor_link():

    link = CommerceLink(
        vendor="Example Vendor",
        destination_url=(
            "https://example.com/product/123"
        ),
    )

    deal = DealCard(
        product_name="Travel Backpack",
        vendor="Example Vendor",
        price=89.0,
        currency="EUR",
        commerce_link=link,
        previous_price=129.0,
        discount_percentage=31.0,
        source="parallel",
    )

    assert deal.product_name == "Travel Backpack"

    assert deal.vendor == "Example Vendor"

    assert deal.price == 89.0

    assert deal.currency == "EUR"

    assert deal.commerce_link.click_url == (
        "https://example.com/product/123"
    )

    assert deal.deal_id


def test_deal_card_rejects_negative_price():

    link = CommerceLink(
        vendor="Example Vendor",
        destination_url=(
            "https://example.com/product/123"
        ),
    )

    with pytest.raises(
        ValueError,
        match="price cannot be negative",
    ):
        DealCard(
            product_name="Travel Backpack",
            vendor="Example Vendor",
            price=-1,
            currency="EUR",
            commerce_link=link,
        )


def test_deal_card_rejects_vendor_mismatch():

    link = CommerceLink(
        vendor="Vendor A",
        destination_url=(
            "https://example.com/product/123"
        ),
    )

    with pytest.raises(
        ValueError,
        match="vendor must match",
    ):
        DealCard(
            product_name="Travel Backpack",
            vendor="Vendor B",
            price=89.0,
            currency="EUR",
            commerce_link=link,
        )


def test_flash_idea_connects_character_to_deal():

    idea = FlashIdea(
        character_id="yeti",
        deal_id="deal-001",
        title="Yeti found this",
        message=(
            "I found a travel backpack "
            "that matches your style."
        ),
    )

    assert idea.character_id == "yeti"

    assert idea.deal_id == "deal-001"

    assert (
        idea.title
        == "Yeti found this"
    )

    assert (
        "travel backpack"
        in idea.message
    )

    assert idea.idea_id