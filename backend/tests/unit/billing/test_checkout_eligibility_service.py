from dataclasses import dataclass

from app.application.payment.checkout_eligibility_service import (
    CheckoutEligibilityService,
)
from app.application.payment.checkout_models import CheckoutEligibility
from app.domain.billing.catalogue import (
    BillingCatalogue,
    BillingPlan,
    BillingPrice,
    BillingScope,
    PlanType,
)


@dataclass
class FakeSubscription:
    status: str
    plan_code: str


class FakeSubscriptionRepository:
    def __init__(self, subscriptions=None):
        self.subscriptions = subscriptions or []

    def get_by_beneficiary_user_id(self, user_id):
        return self.subscriptions


def catalogue():
    return BillingCatalogue(
        plans=[
            BillingPlan(
                plan_code="NORMAL",
                display_name="Normal",
                plan_type=PlanType.NORMAL,
                scope=BillingScope.INDIVIDUAL,
                family_capable=False,
            ),
            BillingPlan(
                plan_code="PREMIUM",
                display_name="Premium",
                plan_type=PlanType.PREMIUM,
                scope=BillingScope.INDIVIDUAL,
                family_capable=False,
            ),
        ],
        prices=[
            BillingPrice(
                plan_code="NORMAL",
                billing_interval="month",
                stripe_price_id="price_normal_monthly",
                currency="eur",
                amount_minor=999,
            ),
            BillingPrice(
                plan_code="PREMIUM",
                billing_interval="month",
                stripe_price_id="price_premium_monthly",
                currency="eur",
                amount_minor=1999,
            ),
        ],
    )


def test_available_plan_allows_direct_checkout():
    service = CheckoutEligibilityService(
        catalogue(),
        FakeSubscriptionRepository(),
    )

    decision = service.evaluate(
        user_id="user-001",
        plan_code="PREMIUM",
        billing_interval="month",
    )

    assert decision.eligibility == CheckoutEligibility.DIRECT_CHECKOUT
    assert decision.price_id == "price_premium_monthly"
    assert decision.beneficiary_user_id == "user-001"
    assert decision.payer_user_id == "user-001"


def test_existing_subscription_blocks_duplicate_purchase():
    repository = FakeSubscriptionRepository(
        [
            FakeSubscription(
                status="active",
                plan_code="PREMIUM",
            )
        ]
    )

    service = CheckoutEligibilityService(
        catalogue(),
        repository,
    )

    decision = service.evaluate(
        user_id="user-001",
        plan_code="PREMIUM",
        billing_interval="month",
    )

    assert decision.eligibility == CheckoutEligibility.ALREADY_SUBSCRIBED


def test_unknown_plan_returns_plan_not_available():
    service = CheckoutEligibilityService(
        catalogue(),
        FakeSubscriptionRepository(),
    )

    decision = service.evaluate(
        user_id="user-001",
        plan_code="UNKNOWN",
        billing_interval="month",
    )

    assert decision.eligibility == CheckoutEligibility.PLAN_NOT_AVAILABLE


def test_parent_can_be_payer_for_different_beneficiary():
    service = CheckoutEligibilityService(
        catalogue(),
        FakeSubscriptionRepository(),
    )

    decision = service.evaluate(
        user_id="parent-001",
        plan_code="PREMIUM",
        billing_interval="month",
        beneficiary_user_id="child-001",
    )

    assert decision.eligibility == CheckoutEligibility.DIRECT_CHECKOUT
    assert decision.payer_user_id == "parent-001"
    assert decision.beneficiary_user_id == "child-001"
