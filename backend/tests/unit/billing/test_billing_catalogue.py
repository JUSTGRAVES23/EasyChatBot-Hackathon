from app.domain.billing.catalogue import (
    BillingCatalogue,
    BillingPlan,
    BillingPrice,
    BillingScope,
    PlanType,
)


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
                plan_code="NORMAL",
                billing_interval="year",
                stripe_price_id="price_normal_yearly",
                currency="eur",
                amount_minor=9999,
            ),
            BillingPrice(
                plan_code="PREMIUM",
                billing_interval="month",
                stripe_price_id="price_premium_monthly",
                currency="eur",
                amount_minor=1999,
            ),
            BillingPrice(
                plan_code="PREMIUM",
                billing_interval="year",
                stripe_price_id="price_premium_yearly",
                currency="eur",
                amount_minor=19999,
            ),
        ],
    )


def test_catalogue_resolves_normal_monthly():
    price = catalogue().get_price(
        plan_code="NORMAL",
        billing_interval="month",
    )

    assert price.stripe_price_id == "price_normal_monthly"
    assert price.amount_minor == 999


def test_catalogue_resolves_premium_yearly():
    price = catalogue().get_price(
        plan_code="PREMIUM",
        billing_interval="year",
    )

    assert price.stripe_price_id == "price_premium_yearly"


def test_catalogue_rejects_unknown_plan():
    try:
        catalogue().get_plan("UNKNOWN")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_catalogue_rejects_unknown_price():
    try:
        catalogue().get_price(
            plan_code="PREMIUM",
            billing_interval="weekly",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")
