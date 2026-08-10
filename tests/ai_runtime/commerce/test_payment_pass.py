"""
Tests for the hackathon PaymentPass.

The PaymentPass is a demo-only checkout handoff.

These tests verify:
- valid construction
- immutable/read-only behaviour
- READY status
- DEMO execution mode
- no executed payment
- validation
- safe checkout URL contract
- deterministic demo rendering
"""

from __future__ import annotations

import pytest

from src.ai_runtime.commerce.payment_pass import (
    PaymentExecutionMode,
    PaymentPass,
    PaymentPassStatus,
)


def make_payment_pass() -> PaymentPass:
    """Create a valid PaymentPass for tests."""

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


def test_payment_pass_creates_valid_demo_handoff():

    payment_pass = make_payment_pass()

    assert (
        payment_pass.payment_pass_id
        == "payment-pass-001"
    )
    assert payment_pass.deal_id == "deal-001"
    assert payment_pass.user_id == "user-001"
    assert payment_pass.product_name == "iPhone 17 Pro"
    assert payment_pass.vendor_name == "Demo Vendor"
    assert payment_pass.amount == 999.99
    assert payment_pass.currency == "EUR"
    assert (
        payment_pass.checkout_url
        == "https://example.com/vendor/iphone17-pro"
    )


def test_payment_pass_is_ready():

    payment_pass = make_payment_pass()

    assert payment_pass.status is PaymentPassStatus.READY
    assert payment_pass.is_ready is True


def test_payment_pass_is_demo_only():

    payment_pass = make_payment_pass()

    assert (
        payment_pass.execution_mode
        is PaymentExecutionMode.DEMO
    )
    assert payment_pass.is_demo_only is True


def test_payment_pass_never_reports_payment_as_executed():

    payment_pass = make_payment_pass()

    assert payment_pass.payment_executed is False


def test_payment_pass_formats_amount():

    payment_pass = make_payment_pass()

    assert (
        payment_pass.display_amount()
        == "EUR 999.99"
    )


def test_payment_pass_renders_demo_handoff():

    payment_pass = make_payment_pass()

    output = payment_pass.render_demo()

    assert "PAYMENT PASS" in output
    assert "Product: iPhone 17 Pro" in output
    assert "Vendor: Demo Vendor" in output
    assert "Amount: EUR 999.99" in output
    assert "Payment status: READY" in output
    assert "Execution mode: DEMO" in output
    assert "[ PROCEED TO CHECKOUT ]" in output
    assert "No payment has been executed." in output
    assert (
        "Vendor checkout remains outside "
        "the hackathon demo."
        in output
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("payment_pass_id", ""),
        ("deal_id", ""),
        ("user_id", ""),
        ("product_name", ""),
        ("vendor_name", ""),
        ("currency", ""),
        ("checkout_url", ""),
    ],
)
def test_payment_pass_rejects_empty_required_text(
    field: str,
    value: str,
):

    values = {
        "payment_pass_id": "payment-pass-001",
        "deal_id": "deal-001",
        "user_id": "user-001",
        "product_name": "iPhone 17 Pro",
        "vendor_name": "Demo Vendor",
        "amount": 999.99,
        "currency": "EUR",
        "checkout_url": (
            "https://example.com/vendor/iphone17-pro"
        ),
    }

    values[field] = value

    with pytest.raises(
        ValueError,
        match=f"PaymentPass {field} cannot be empty",
    ):
        PaymentPass(**values)


def test_payment_pass_rejects_negative_amount():

    with pytest.raises(
        ValueError,
        match="amount cannot be negative",
    ):
        PaymentPass(
            payment_pass_id="payment-pass-001",
            deal_id="deal-001",
            user_id="user-001",
            product_name="iPhone 17 Pro",
            vendor_name="Demo Vendor",
            amount=-1.0,
            currency="EUR",
            checkout_url=(
                "https://example.com/vendor/iphone17-pro"
            ),
        )


@pytest.mark.parametrize(
    "checkout_url",
    [
        "ftp://example.com/checkout",
        "vendor.example.com/checkout",
    ],
)
def test_payment_pass_rejects_non_http_checkout_url(
    checkout_url: str,
):

    with pytest.raises(
        ValueError,
        match="checkout_url must use HTTP or HTTPS",
    ):
        PaymentPass(
            payment_pass_id="payment-pass-001",
            deal_id="deal-001",
            user_id="user-001",
            product_name="iPhone 17 Pro",
            vendor_name="Demo Vendor",
            amount=999.99,
            currency="EUR",
            checkout_url=checkout_url,
        )


def test_payment_pass_rejects_non_demo_execution_mode():

    with pytest.raises(
        ValueError,
        match="execution_mode must be DEMO",
    ):
        PaymentPass(
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
            execution_mode="LIVE",
        )


def test_payment_pass_rejects_non_ready_status():

    with pytest.raises(
        ValueError,
        match="status must be READY",
    ):
        PaymentPass(
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
            status="EXECUTED",
        )


def test_payment_pass_is_immutable():

    payment_pass = make_payment_pass()

    with pytest.raises(AttributeError):
        payment_pass.amount = 100.0