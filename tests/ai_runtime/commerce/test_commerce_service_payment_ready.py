"""
Regression tests for the CommerceService payment boundary.
"""

import pytest

from src.ai_runtime.commerce.payment_pass import (
    PaymentPass,
)

from src.ai_runtime.commerce.service import (
    CommerceService,
)


def make_payment_pass() -> PaymentPass:
    """Create a valid demo payment pass."""

    return PaymentPass(
        payment_pass_id="payment-pass-001",
        deal_id="deal-001",
        user_id="user-001",
        product_name="iPhone 17 Pro",
        vendor_name="Demo Vendor",
        amount=999.99,
        currency="EUR",
        checkout_url=(
            "https://example.com/vendor/iphone17-pro"
        ),
    )


def test_commerce_service_prepares_demo_payment():

    payment_pass = make_payment_pass()

    result = CommerceService().prepare_payment(
        payment_pass
    )

    assert result is payment_pass
    assert result.is_ready is True
    assert result.is_demo_only is True
    assert result.payment_executed is False


def test_commerce_service_does_not_change_payment_pass():

    payment_pass = make_payment_pass()

    result = CommerceService().prepare_payment(
        payment_pass
    )

    assert result.payment_pass_id == payment_pass.payment_pass_id
    assert result.deal_id == payment_pass.deal_id
    assert result.user_id == payment_pass.user_id
    assert result.amount == payment_pass.amount
    assert result.currency == payment_pass.currency
    assert result.checkout_url == payment_pass.checkout_url


def test_commerce_service_rejects_non_ready_payment_pass():

    class InvalidPaymentPass:
        is_ready = False
        is_demo_only = True

    with pytest.raises(
        ValueError,
        match="PaymentPass must be READY",
    ):
        CommerceService().prepare_payment(
            InvalidPaymentPass()
        )


def test_commerce_service_rejects_non_demo_payment():

    class InvalidPaymentPass:
        is_ready = True
        is_demo_only = False

    with pytest.raises(
        ValueError,
        match="DEMO execution mode",
    ):
        CommerceService().prepare_payment(
            InvalidPaymentPass()
        )