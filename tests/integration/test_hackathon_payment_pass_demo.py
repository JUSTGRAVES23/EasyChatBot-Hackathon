"""
Integration acceptance tests for the hackathon Payment Pass.

The test verifies the complete safe commerce path:

FlashDealCard
    ↓
FlashDealCommerce
    ↓
PaymentPass
    ↓
CommerceService
    ↓
READY / DEMO
    ↓
Vendor checkout

No real payment is executed.
"""

from __future__ import annotations

from src.ai_runtime.commerce.flash_deal_commerce import (
    FlashDealCommerce,
)

from src.ai_runtime.commerce.payment_pass import (
    PaymentExecutionMode,
    PaymentPassStatus,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)

from src.ai_runtime.discovery.flash_deal_card import (
    FlashDealCard,
)


def make_card() -> FlashDealCard:
    """Create deterministic hackathon deal data."""

    return FlashDealCard(
        deal_id="deal-payment-demo-001",
        character_id="yeti",
        character_name="Yeti",
        character_message=(
            "Look what I found! "
            "This could be perfect for you."
        ),
        product_name="iPhone 17 Pro",
        product_image_url=(
            "https://example.com/demo/iphone17-pro.jpg"
        ),
        tagline="Pro. Beautiful. Powerful.",
        highlights=(
            "Pro camera system",
            "High-performance chip",
            "All-day battery life",
            "Premium display",
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


def test_complete_payment_pass_flow():

    card = make_card()

    commerce = FlashDealCommerce()

    payment_pass = commerce.create_payment_pass(
        user_id="user-001",
        card=card,
    )

    prepared = CommerceService().prepare_payment(
        payment_pass
    )

    assert prepared is payment_pass

    assert prepared.deal_id == card.deal_id
    assert prepared.user_id == "user-001"

    assert (
        prepared.product_name
        == card.product_name
    )

    assert (
        prepared.vendor_name
        == card.vendor_name
    )

    assert (
        prepared.amount
        == card.current_price
    )

    assert (
        prepared.currency
        == card.currency
    )

    assert (
        prepared.checkout_url
        == card.get_deal_url
    )

    assert (
        prepared.status
        is PaymentPassStatus.READY
    )

    assert (
        prepared.execution_mode
        is PaymentExecutionMode.DEMO
    )

    assert prepared.payment_executed is False


def test_payment_pass_cannot_become_executed():

    card = make_card()

    payment_pass = (
        FlashDealCommerce().create_payment_pass(
            user_id="user-001",
            card=card,
        )
    )

    assert payment_pass.payment_executed is False

    assert (
        payment_pass.status
        is PaymentPassStatus.READY
    )

    assert (
        payment_pass.execution_mode
        is PaymentExecutionMode.DEMO
    )


def test_payment_pass_preserves_vendor_checkout():

    card = make_card()

    payment_pass = (
        FlashDealCommerce().create_payment_pass(
            user_id="user-001",
            card=card,
        )
    )

    prepared = CommerceService().prepare_payment(
        payment_pass
    )

    assert (
        prepared.checkout_url
        == "https://example.com/vendor/iphone17-pro"
    )


def test_payment_pass_demo_render_is_explicit():

    card = make_card()

    payment_pass = (
        FlashDealCommerce().create_payment_pass(
            user_id="user-001",
            card=card,
        )
    )

    prepared = CommerceService().prepare_payment(
        payment_pass
    )

    output = prepared.render_demo()

    assert "PAYMENT PASS" in output
    assert "Payment status: READY" in output
    assert "Execution mode: DEMO" in output
    assert "No payment has been executed." in output
    assert (
        "Vendor checkout remains outside "
        "the hackathon demo."
        in output
    )