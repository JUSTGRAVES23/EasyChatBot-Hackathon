from app.infrastructure.persistence.billing_models import (
    BillingPlanRecord,
    BillingPriceRecord,
    ParentChildRelationshipRecord,
    ParentalConsentRecord,
    PaymentApprovalRequestRecord,
    SubscriptionRecord,
    EntitlementRecord,
    StripeWebhookEventRecord,
)


def test_p5b1_models_register_expected_tables():
    expected = {
        "billing_plans",
        "billing_prices",
        "parent_child_relationships",
        "parental_consents",
        "payment_approval_requests",
        "subscriptions",
        "entitlements",
        "stripe_webhook_events",
    }
    actual = {
        BillingPlanRecord.__tablename__,
        BillingPriceRecord.__tablename__,
        ParentChildRelationshipRecord.__tablename__,
        ParentalConsentRecord.__tablename__,
        PaymentApprovalRequestRecord.__tablename__,
        SubscriptionRecord.__tablename__,
        EntitlementRecord.__tablename__,
        StripeWebhookEventRecord.__tablename__,
    }
    assert actual == expected


def test_p5b1_subscription_separates_payer_and_beneficiary():
    columns = {column.name for column in SubscriptionRecord.__table__.columns}
    assert "payer_user_id" in columns
    assert "beneficiary_user_id" in columns


def test_p5b1_relationship_supports_multiple_guardians_per_child():
    assert "parent_user_id" in ParentChildRelationshipRecord.__table__.columns
    assert "child_user_id" in ParentChildRelationshipRecord.__table__.columns
    assert "uq_parent_child_relationship" in {
        constraint.name for constraint in ParentChildRelationshipRecord.__table__.constraints
    }
