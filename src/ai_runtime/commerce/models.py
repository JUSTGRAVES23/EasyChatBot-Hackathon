"""
Hackathon commerce contracts.

These contracts define the boundary between EasyChatBot's
discovery experience and an eventual commerce/payment
integration.

EasyChatBot does not implement a marketplace here.

The external commerce provider is responsible for the
actual payment and vendor transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class CommerceActionType(str, Enum):
    """
    Supported commerce actions.
    """

    VIEW_PRODUCT = "view_product"

    INITIATE_PURCHASE = "initiate_purchase"


class CommerceActionStatus(str, Enum):
    """
    Result status of a commerce action.
    """

    READY = "ready"

    REDIRECT = "redirect"

    REJECTED = "rejected"


@dataclass(frozen=True)
class CommerceAction:
    """
    Explicit request to perform a commerce action.

    This is an application-level contract.

    It is intentionally independent from Stripe, Amazon,
    OLX, or any other vendor.
    """

    user_id: str

    deal_id: str

    action_type: CommerceActionType

    destination_url: str

    action_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    metadata: dict[str, str] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError(
                "Commerce action user_id cannot be empty."
            )

        if not self.deal_id.strip():
            raise ValueError(
                "Commerce action deal_id cannot be empty."
            )

        if not self.destination_url.strip():
            raise ValueError(
                "Commerce action destination URL "
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
                "Commerce action destination URL "
                "must use HTTP or HTTPS."
            )


@dataclass(frozen=True)
class CommerceActionResult:
    """
    Provider-independent result of a commerce action.
    """

    action_id: str

    deal_id: str

    status: CommerceActionStatus

    next_url: str | None = None

    message: str | None = None

    metadata: dict[str, str] = field(
        default_factory=dict
    )