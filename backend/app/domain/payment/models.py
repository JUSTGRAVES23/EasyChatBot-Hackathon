from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class BillingInterval(str, Enum):
    MONTH = "month"
    YEAR = "year"


class CheckoutMode(str, Enum):
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"


class SubscriptionStatus(str, Enum):
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


@dataclass(frozen=True)
class PaymentPlan:
    key: str
    display_name: str
    stripe_price_id: str | None
    mode: CheckoutMode
    interval: BillingInterval | None = None
    active: bool = True


@dataclass(frozen=True)
class CheckoutRequest:
    user_id: str
    price_id: str
    mode: CheckoutMode
    success_url: str
    cancel_url: str
    payer_user_id: str | None = None
    plan_code: str | None = None


@dataclass(frozen=True)
class CheckoutSession:
    provider_session_id: str
    checkout_url: str


@dataclass(frozen=True)
class BillingPortalSession:
    provider_session_id: str
    portal_url: str


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    event_type: str
    payload: dict[str, Any]
