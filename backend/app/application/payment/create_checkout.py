from __future__ import annotations

from app.application.payment.checkout_models import CheckoutEligibility
from app.application.payment.ports import PaymentProvider
from app.domain.payment.models import CheckoutMode, CheckoutRequest


class CreateCheckout:
    """Create a Stripe Checkout session after eligibility has been established.

    This service does not determine eligibility itself and does not grant
    entitlements. PaymentProvider remains the Stripe abstraction boundary.
    """

    def __init__(
        self,
        provider: PaymentProvider,
        eligibility_service,
    ) -> None:
        if provider is None:
            raise ValueError("provider cannot be None.")

        if eligibility_service is None:
            raise ValueError("eligibility_service cannot be None.")

        self.provider = provider
        self.eligibility_service = eligibility_service

    def execute(
        self,
        *,
        user_id: str,
        plan_code: str,
        billing_interval: str,
        success_url: str,
        cancel_url: str,
        stripe_customer_id: str | None = None,
        beneficiary_user_id: str | None = None,
    ):
        decision = self.eligibility_service.evaluate(
            user_id=user_id,
            plan_code=plan_code,
            billing_interval=billing_interval,
            beneficiary_user_id=beneficiary_user_id,
        )

        if decision.eligibility != CheckoutEligibility.DIRECT_CHECKOUT:
            raise ValueError(
                f"Checkout is not permitted: "
                f"{decision.eligibility.value}."
            )

        if not decision.price_id:
            raise ValueError(
                "Checkout decision is missing price_id."
            )

        beneficiary = (
            decision.beneficiary_user_id
            or beneficiary_user_id
            or user_id
        )

        payer = (
            decision.payer_user_id
            or user_id
        )

        request = CheckoutRequest(
            user_id=beneficiary,
            price_id=decision.price_id,
            mode=CheckoutMode.SUBSCRIPTION,
            success_url=success_url,
            cancel_url=cancel_url,
            payer_user_id=payer,
            plan_code=decision.plan_code,
        )

        # CheckoutRequest currently carries the beneficiary identity only.
        # Payer/plan metadata is added at the provider boundary through the
        # provider implementation in the next integration slice.
        #
        # The service deliberately does not access Stripe SDK objects.

        return self.provider.create_checkout_session(
            request,
            customer_id=stripe_customer_id,
        )


__all__ = ["CreateCheckout"]
