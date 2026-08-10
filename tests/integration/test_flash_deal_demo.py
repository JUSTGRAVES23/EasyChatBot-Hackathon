"""
Integration test for the EasyChatBot Flash Deal demonstration.

Validates the complete hackathon discovery presentation:

Memory
    ↓
DealCard
    ↓
Personal relevance
    ↓
Character
    ↓
FlashDealCard
    ↓
Commerce actions
"""

from src.ai_runtime.discovery.flash_deal_demo import (
    build_demo_flash_deal_card,
    render_demo_flash_deal_card,
)


def test_demo_builds_flash_deal_card():

    card = build_demo_flash_deal_card()

    assert card.character_id == "yeti"

    assert card.character_name == "Yeti"

    assert card.product_name == "iPhone 17 Pro"

    assert card.vendor_name == "Demo Vendor"

    assert card.current_price == 999.99

    assert card.previous_price == 1199.00

    assert card.discount_percentage == 17.0

    assert card.has_discount is True


def test_demo_contains_personalisation():

    card = build_demo_flash_deal_card()

    assert (
        "mobile photography"
        in card.relevance_reason
    )

    assert (
        card.metadata["memory_type"]
        == "preference"
    )


def test_demo_contains_both_commerce_actions():

    card = build_demo_flash_deal_card()

    assert card.get_deal_url

    assert card.more_information_url

    assert (
        card.get_deal_url
        == card.more_information_url
    )


def test_demo_render_contains_user_facing_sections():

    card = build_demo_flash_deal_card()

    output = render_demo_flash_deal_card(
        card
    )

    assert "NEW FIND!" in output

    assert "Yeti" in output

    assert "iPhone 17 Pro" in output

    assert "PRICE" in output

    assert "WHY THIS IS RELEVANT TO YOU" in output

    assert "AVAILABLE FROM" in output

    assert "GET DEAL" in output

    assert "MORE INFORMATION" in output


def test_demo_is_explicitly_marked_as_demo_data():

    output = render_demo_flash_deal_card()

    assert (
        "deterministic hackathon demo data"
        in output
    )