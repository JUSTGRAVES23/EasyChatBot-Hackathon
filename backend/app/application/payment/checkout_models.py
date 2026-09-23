from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CheckoutEligibility(str, Enum):
    DIRECT_CHECKOUT = "direct_checkout"
    PARENT_APPROVAL_REQUIRED = "parent_approval_required"
    ALREADY_SUBSCRIBED = "already_subscribed"
    NOT_ELIGIBLE = "not_eligible"
    PLAN_NOT_AVAILABLE = "plan_not_available"


@dataclass(frozen=True)
class CheckoutDecision:
    eligibility: CheckoutEligibility
    plan_code: str
    price_id: str | None = None
    beneficiary_user_id: str | None = None
    payer_user_id: str | None = None


__all__ = [
    "CheckoutDecision",
    "CheckoutEligibility",
]
