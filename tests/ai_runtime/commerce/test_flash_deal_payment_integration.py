"""
Tests for Flash Deal commerce integration.

These tests verify that a FlashDealCard can produce both:
- the existing CommerceAction
- the new demo-only PaymentPass

No payment is executed.
"""

import pytest

from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.models import (
    CommerceActionType,
)

from src.ai_runtime.commerce.payment_pass import (
    PaymentExecutionMode,
    PaymentPassStatus,
)

from src.ai_runtime.discovery.flash_deal_card import (
    FlashDealCard,
)


def make_card() -> FlashDealCard:
    """Create a deterministic FlashDealCard for tests."""

    return FlashDealCard(
        deal_id="deal-001",
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "Look what I found!"
        ),
        product_name="iPhone 17 Pro",
        product_image_url=(
            "https://example.com/demo/iphone17-pro.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=(
            "Pro camera system",
            "High-performance chip",
        ),
        current_price=999.99,
        currency="EUR",
        previous_price=1199.00,
        discount_percentage=17.0,
        savings=199.01,
        relevance_reason=(
            "Matches the user's preference for "
            "powerful mobile photography devices."
        ),
        vendor_name="Demo Vendor",
        more_information_url=(
            "https://example.com/vendor/iphone17-pro"
        ),
        get_deal_url=(
            "https://example.com/vendor/iphone17-pro"
        ),
    )


def test_flash_deal_commerce_still_creates_existing_action():

    card = make_card()

    action = FlashDealCommerce().create_action(
        user_id="user-001",
        card=card,
    )

    assert action.user_id == "user-001"
    assert action.deal_id == "deal-001"
    assert (
        action.action_type
        is CommerceActionType.INITIATE_PURCHASE
    )
    assert (
        action.destination_url
        == card.get_deal_url
    )


def test_flash_deal_creates_demo_payment_pass():

    card = make_card()

    payment_pass = (
        FlashDealCommerce().create_payment_pass(
            user_id="user-001",
            card=card,
            payment_pass_id="payment-pass-001",
        )
    )

    assert (
        payment_pass.payment_pass_id
        == "payment-pass-001"
    )
    assert payment_pass.user_id == "user-001"
    assert payment_pass.deal_id == card.deal_id
    assert payment_pass.product_name == card.product_name
    assert payment_pass.vendor_name == card.vendor_name
    assert payment_pass.amount == card.current_price
    assert payment_pass.currency == card.currency
    assert (
        payment_pass.checkout_url
        == card.get_deal_url
    )

    assert (
        payment_pass.status
        is PaymentPassStatus.READY
    )

    assert (
        payment_pass.execution_mode
        is PaymentExecutionMode.DEMO
    )

    assert payment_pass.payment_executed is False


def test_flash_deal_payment_pass_preserves_checkout_boundary():

    card = make_card()

    payment_pass = (
        FlashDealCommerce().create_payment_pass(
            user_id="user-001",
            card=card,
        )
    )

    assert (
        payment_pass.checkout_url
        == card.get_deal_url
    )

    assert payment_pass.payment_executed is False


def test_flash_deal_payment_pass_rejects_empty_user():

    with pytest.raises(
        ValueError,
        match="Commerce user_id cannot be empty",
    ):
        FlashDealCommerce().create_payment_pass(
            user_id="",
            card=make_card(),
        )