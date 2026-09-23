from app.domain.payment.models import CheckoutMode, CheckoutRequest


def test_checkout_request_preserves_beneficiary_payer_and_plan():
    request = CheckoutRequest(
        user_id="child-001",
        price_id="price_premium_monthly",
        mode=CheckoutMode.SUBSCRIPTION,
        success_url="https://easyworld.test/success",
        cancel_url="https://easyworld.test/cancel",
        payer_user_id="parent-001",
        plan_code="PREMIUM",
    )

    assert request.user_id == "child-001"
    assert request.payer_user_id == "parent-001"
    assert request.plan_code == "PREMIUM"


def test_checkout_request_supports_individual_purchase():
    request = CheckoutRequest(
        user_id="user-001",
        price_id="price_normal_monthly",
        mode=CheckoutMode.SUBSCRIPTION,
        success_url="https://easyworld.test/success",
        cancel_url="https://easyworld.test/cancel",
        payer_user_id="user-001",
        plan_code="NORMAL",
    )

    assert request.user_id == "user-001"
    assert request.payer_user_id == "user-001"
    assert request.plan_code == "NORMAL"
