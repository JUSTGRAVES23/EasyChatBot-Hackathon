from __future__ import annotations

from app.application.payment.checkout_models import (
    CheckoutDecision,
    CheckoutEligibility,
)


class CheckoutEligibilityService:
    """Determine whether a user may initiate a billing checkout.

    This service does not call Stripe and does not create access.
    """

    def __init__(
        self,
        billing_catalogue,
        subscription_repository,
    ) -> None:
        if billing_catalogue is None:
            raise ValueError("billing_catalogue cannot be None.")

        if subscription_repository is None:
            raise ValueError("subscription_repository cannot be None.")

        self.billing_catalogue = billing_catalogue
        self.subscription_repository = subscription_repository

    def evaluate(
        self,
        *,
        user_id: str,
        plan_code: str,
        billing_interval: str,
        beneficiary_user_id: str | None = None,
    ) -> CheckoutDecision:
        if not user_id:
            raise ValueError("user_id cannot be empty.")

        if not plan_code:
            raise ValueError("plan_code cannot be empty.")

        if not billing_interval:
            raise ValueError("billing_interval cannot be empty.")

        try:
            price = self.billing_catalogue.get_price(
                plan_code=plan_code,
                billing_interval=billing_interval,
            )
        except ValueError:
            return CheckoutDecision(
                eligibility=CheckoutEligibility.PLAN_NOT_AVAILABLE,
                plan_code=plan_code,
                beneficiary_user_id=beneficiary_user_id or user_id,
            )

        beneficiary = beneficiary_user_id or user_id

        existing = self.subscription_repository.get_by_beneficiary_user_id(
            beneficiary
        )

        active_statuses = {
            "trialing",
            "active",
            "past_due",
        }

        if any(
            subscription.status in active_statuses
            and subscription.plan_code == plan_code
            for subscription in existing
        ):
            return CheckoutDecision(
                eligibility=CheckoutEligibility.ALREADY_SUBSCRIBED,
                plan_code=plan_code,
                price_id=price.stripe_price_id,
                beneficiary_user_id=beneficiary,
                payer_user_id=user_id,
            )

        # Current policy:
        # A beneficiary purchasing for themselves can proceed directly.
        # Parent/guardian approval rules will be connected through the
        # relationship/policy layer in the next slice.
        return CheckoutDecision(
            eligibility=CheckoutEligibility.DIRECT_CHECKOUT,
            plan_code=plan_code,
            price_id=price.stripe_price_id,
            beneficiary_user_id=beneficiary,
            payer_user_id=user_id,
        )


__all__ = ["CheckoutEligibilityService"]
