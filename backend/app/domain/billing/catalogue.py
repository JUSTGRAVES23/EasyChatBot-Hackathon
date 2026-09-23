from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlanType(str, Enum):
    NORMAL = "normal"
    PREMIUM = "premium"


class BillingScope(str, Enum):
    INDIVIDUAL = "individual"
    FAMILY = "family"


@dataclass(frozen=True)
class BillingPlan:
    plan_code: str
    display_name: str
    plan_type: PlanType
    scope: BillingScope
    family_capable: bool
    active: bool = True


@dataclass(frozen=True)
class BillingPrice:
    plan_code: str
    billing_interval: str
    stripe_price_id: str
    currency: str
    amount_minor: int
    active: bool = True


class BillingCatalogue:
    """Application-facing billing catalogue.

    Stripe price IDs are configuration/data, not business logic.
    """

    def __init__(
        self,
        plans: list[BillingPlan],
        prices: list[BillingPrice],
    ) -> None:
        self._plans = {
            plan.plan_code: plan
            for plan in plans
        }

        self._prices = {
            (price.plan_code, price.billing_interval): price
            for price in prices
        }

    def get_plan(self, plan_code: str) -> BillingPlan:
        if not plan_code:
            raise ValueError("plan_code cannot be empty.")

        try:
            return self._plans[plan_code]
        except KeyError:
            raise ValueError(
                f"Unknown billing plan: {plan_code!r}."
            )

    def get_price(
        self,
        *,
        plan_code: str,
        billing_interval: str,
    ) -> BillingPrice:
        plan = self.get_plan(plan_code)

        if not plan.active:
            raise ValueError(
                f"Billing plan is inactive: {plan_code!r}."
            )

        key = (plan_code, billing_interval)

        try:
            price = self._prices[key]
        except KeyError:
            raise ValueError(
                "No billing price configured for "
                f"{plan_code!r} / {billing_interval!r}."
            )

        if not price.active:
            raise ValueError(
                "Billing price is inactive for "
                f"{plan_code!r} / {billing_interval!r}."
            )

        return price


__all__ = [
    "BillingCatalogue",
    "BillingPlan",
    "BillingPrice",
    "BillingScope",
    "PlanType",
]
