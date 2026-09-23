from dataclasses import dataclass

from app.application.payment.authorization_models import (
    AuthorizationDecision,
)
from app.application.payment.payment_authorization_service import (
    PaymentAuthorizationService,
)


@dataclass
class FakeRelationship:
    parent_user_id: str
    child_user_id: str


class FakeRelationshipRepository:
    def __init__(self, relationships=None):
        self.relationships = relationships or []

    def get_active_parents_for_child(self, child_user_id):
        return self.relationships


class FakeConsentRepository:
    def __init__(self, approved=None):
        self.approved = approved or set()

    def has_active_payment_consent(
        self,
        *,
        parent_user_id,
        child_user_id,
    ):
        return (parent_user_id, child_user_id) in self.approved


def test_adult_can_be_authorized_directly():
    service = PaymentAuthorizationService(
        FakeRelationshipRepository(),
        FakeConsentRepository(),
    )

    decision = service.evaluate(
        beneficiary_user_id="adult-001",
        requires_parental_authorization=False,
    )

    assert decision.decision == AuthorizationDecision.AUTHORIZED
    assert decision.payer_user_id == "adult-001"


def test_child_without_guardian_requires_no_guardian_result():
    service = PaymentAuthorizationService(
        FakeRelationshipRepository(),
        FakeConsentRepository(),
    )

    decision = service.evaluate(
        beneficiary_user_id="child-001",
        requires_parental_authorization=True,
    )

    assert decision.decision == AuthorizationDecision.NO_GUARDIAN
    assert decision.payer_user_id is None


def test_child_with_guardian_but_without_consent_requires_approval():
    relationships = FakeRelationshipRepository(
        [
            FakeRelationship(
                parent_user_id="parent-001",
                child_user_id="child-001",
            )
        ]
    )

    service = PaymentAuthorizationService(
        relationships,
        FakeConsentRepository(),
    )

    decision = service.evaluate(
        beneficiary_user_id="child-001",
        requires_parental_authorization=True,
    )

    assert decision.decision == AuthorizationDecision.APPROVAL_REQUIRED
    assert decision.payer_user_id is None


def test_child_with_active_payment_consent_is_authorized():
    relationships = FakeRelationshipRepository(
        [
            FakeRelationship(
                parent_user_id="parent-001",
                child_user_id="child-001",
            )
        ]
    )

    consents = FakeConsentRepository(
        {
            ("parent-001", "child-001"),
        }
    )

    service = PaymentAuthorizationService(
        relationships,
        consents,
    )

    decision = service.evaluate(
        beneficiary_user_id="child-001",
        requires_parental_authorization=True,
    )

    assert decision.decision == AuthorizationDecision.AUTHORIZED
    assert decision.beneficiary_user_id == "child-001"
    assert decision.payer_user_id == "parent-001"


def test_multiple_guardians_can_authorize_same_child():
    relationships = FakeRelationshipRepository(
        [
            FakeRelationship(
                parent_user_id="parent-001",
                child_user_id="child-001",
            ),
            FakeRelationship(
                parent_user_id="parent-002",
                child_user_id="child-001",
            ),
        ]
    )

    consents = FakeConsentRepository(
        {
            ("parent-002", "child-001"),
        }
    )

    service = PaymentAuthorizationService(
        relationships,
        consents,
    )

    decision = service.evaluate(
        beneficiary_user_id="child-001",
        requires_parental_authorization=True,
    )

    assert decision.decision == AuthorizationDecision.AUTHORIZED
    assert decision.payer_user_id == "parent-002"
