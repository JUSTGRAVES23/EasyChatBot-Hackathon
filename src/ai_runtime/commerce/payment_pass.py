"""
Hackathon Payment Pass.

This module defines the minimal payment handoff contract required
for the EasyChatBot hackathon.

Architecture:

FlashDealCard
    |
    v
CommerceService
    |
    v
PaymentPass
    |
    v
Vendor / Checkout URL

The PaymentPass is a DEMO-ONLY checkout handoff.

It does not:
- execute payments
- call payment providers
- store payment credentials
- store card numbers
- store bank information
- create payment transactions
- confirm a purchase
- perform autonomous commerce actions

Important invariant:

PaymentPass != PaymentTransaction

The hackathon can demonstrate that a checkout/payment journey is
ready without actually charging the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PaymentPassStatus(str, Enum):
    """Status of the demo payment handoff."""

    READY = "READY"


class PaymentExecutionMode(str, Enum):
    """Execution mode for the hackathon payment boundary."""

    DEMO = "DEMO"


@dataclass(frozen=True)
class PaymentPass:
    """
    Immutable payment handoff contract for the hackathon.

    This object represents a checkout journey that is ready to be
    handed to the vendor. It does not represent an executed payment.
    """

    payment_pass_id: str
    deal_id: str
    user_id: str

    product_name: str
    vendor_name: str

    amount: float
    currency: str

    checkout_url: str

    status: PaymentPassStatus = PaymentPassStatus.READY
    execution_mode: PaymentExecutionMode = (
        PaymentExecutionMode.DEMO
    )

    def __post_init__(self) -> None:
        """Validate the payment handoff contract."""

        required_text_fields = {
            "payment_pass_id": self.payment_pass_id,
            "deal_id": self.deal_id,
            "user_id": self.user_id,
            "product_name": self.product_name,
            "vendor_name": self.vendor_name,
            "currency": self.currency,
            "checkout_url": self.checkout_url,
        }

        for field_name, value in required_text_fields.items():
            if not value.strip():
                raise ValueError(
                    f"PaymentPass {field_name} cannot be empty."
                )

        if self.amount < 0:
            raise ValueError(
                "PaymentPass amount cannot be negative."
            )

        if not (
            self.checkout_url.startswith("https://")
            or self.checkout_url.startswith("http://")
        ):
            raise ValueError(
                "PaymentPass checkout_url must use "
                "HTTP or HTTPS."
            )

        if self.status is not PaymentPassStatus.READY:
            raise ValueError(
                "Hackathon PaymentPass status must be READY."
            )

        if self.execution_mode is not PaymentExecutionMode.DEMO:
            raise ValueError(
                "Hackathon PaymentPass execution_mode must be DEMO."
            )

    @property
    def is_ready(self) -> bool:
        """Return whether the checkout handoff is ready."""

        return self.status is PaymentPassStatus.READY

    @property
    def is_demo_only(self) -> bool:
        """Return whether the pass is restricted to demo execution."""

        return (
            self.execution_mode
            is PaymentExecutionMode.DEMO
        )

    @property
    def payment_executed(self) -> bool:
        """
        Explicitly indicate whether payment was executed.

        The hackathon PaymentPass can never represent an executed
        payment. It is a checkout handoff only.
        """

        return False

    def display_amount(self) -> str:
        """Return a UI-friendly amount."""

        return (
            f"{self.currency} "
            f"{self.amount:.2f}"
        )

    def render_demo(self) -> str:
        """
        Render the payment handoff for the hackathon demonstration.

        The output deliberately makes the non-execution boundary
        explicit to judges and users.
        """

        return "\n".join(
            [
                "PAYMENT PASS",
                "-" * 72,
                f"Product: {self.product_name}",
                f"Vendor: {self.vendor_name}",
                f"Amount: {self.display_amount()}",
                "",
                f"Payment status: {self.status.value}",
                (
                    "Execution mode: "
                    f"{self.execution_mode.value}"
                ),
                "",
                "[ PROCEED TO CHECKOUT ]",
                "",
                "No payment has been executed.",
                (
                    "Vendor checkout remains outside "
                    "the hackathon demo."
                ),
            ]
        )