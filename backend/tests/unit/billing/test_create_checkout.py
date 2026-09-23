from dataclasses import dataclass

from app.application.payment.checkout_models import (
    CheckoutDecision,
    CheckoutEligibility,
)
from app.application.payment.create_checkout import CreateCheckout
from app.domain.payment.models import CheckoutSession


@dataclass
class FakeProvider:
    calls: list

    def create_checkout_session(self, request, *, customer_id):
        self.calls.append(
            {
                "request": request,
                "customer_id": customer_id,
            }
        )

        return CheckoutSession(
            provider_session_id="cs_test_001",
            checkout_url="https://checkout.test/session",
        )


class FakeEligibilityService:
    def __init__(self, decision):
        self.decision = decision
        self.calls = []

    def evaluate(self, **kwargs):
        self.calls.append(kwargs)
        return self.decision


def test_create_checkout_delegates_to_payment_provider():
    provider = FakeProvider(calls=[])

    eligibility = FakeEligibilityService(
        CheckoutDecision(
            eligibility=CheckoutEligibility.DIRECT_CHECKOUT,
            plan_code="PREMIUM",
            price_id="price_premium_monthly",
            beneficiary_user_id="user-001",
            payer_user_id="user-001",
        )
    )

    service = CreateCheckout(
        provider,
        eligibility,
    )

    result = service.execute(
        user_id="user-001",
        plan_code="PREMIUM",
        billing_interval="month",
        success_url="https://easyworld.test/success",
        cancel_url="https://easyworld.test/cancel",
        stripe_customer_id="cus_test_001",
    )

    assert result.provider_session_id == "cs_test_001"
    assert len(provider.calls) == 1

    call = provider.calls[0]

    assert call["customer_id"] == "cus_test_001"
    assert call["request"].user_id == "user-001"
    assert call["request"].price_id == "price_premium_monthly"


def test_create_checkout_preserves_parent_payer_and_child_beneficiary():
    provider = FakeProvider(calls=[])

    eligibility = FakeEligibilityService(
        CheckoutDecision(
            eligibility=CheckoutEligibility.DIRECT_CHECKOUT,
            plan_code="PREMIUM",
            price_id="price_premium_monthly",
            beneficiary_user_id="child-001",
            payer_user_id="parent-001",
        )
    )

    service = CreateCheckout(
        provider,
        eligibility,
    )

    service.execute(
        user_id="parent-001",
        plan_code="PREMIUM",
        billing_interval="month",
        success_url="https://easyworld.test/success",
        cancel_url="https://easyworld.test/cancel",
        beneficiary_user_id="child-001",
    )

    assert provider.calls[0]["request"].user_id == "child-001"


def test_create_checkout_rejects_parent_approval_required():
    provider = FakeProvider(calls=[])

    eligibility = FakeEligibilityService(
        CheckoutDecision(
            eligibility=CheckoutEligibility.PARENT_APPROVAL_REQUIRED,
            plan_code="PREMIUM",
            beneficiary_user_id="child-001",
            payer_user_id="parent-001",
        )
    )

    service = CreateCheckout(
        provider,
        eligibility,
    )

    try:
        service.execute(
            user_id="child-001",
            plan_code="PREMIUM",
            billing_interval="month",
            success_url="https://easyworld.test/success",
            cancel_url="https://easyworld.test/cancel",
        )
    except ValueError as exc:
        assert "parent_approval_required" in str(exc)
    else:
        raise AssertionError("Expected checkout to be rejected")


def test_create_checkout_rejects_already_subscribed():
    provider = FakeProvider(calls=[])

    eligibility = FakeEligibilityService(
        CheckoutDecision(
            eligibility=CheckoutEligibility.ALREADY_SUBSCRIBED,
            plan_code="PREMIUM",
            price_id="price_premium_monthly",
            beneficiary_user_id="user-001",
            payer_user_id="user-001",
        )
    )

    service = CreateCheckout(
        provider,
        eligibility,
    )

    try:
        service.execute(
            user_id="user-001",
            plan_code="PREMIUM",
            billing_interval="month",
            success_url="https://easyworld.test/success",
            cancel_url="https://easyworld.test/cancel",
        )
    except ValueError as exc:
        assert "already_subscribed" in str(exc)
    else:
        raise AssertionError("Expected checkout to be rejected")
