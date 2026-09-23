from __future__ import annotations

from app.application.payment.authorization_models import (
    AuthorizationDecision,
    PaymentAuthorizationDecision,
)


class PaymentAuthorizationService:
    """Determine whether a beneficiary may initiate paid checkout.

    Relationship, consent and payment authorization remain separate concepts.
    """

    def __init__(
        self,
        relationship_repository,
        consent_repository,
    ) -> None:
        if relationship_repository is None:
            raise ValueError("relationship_repository cannot be None.")

        if consent_repository is None:
            raise ValueError("consent_repository cannot be None.")

        self.relationship_repository = relationship_repository
        self.consent_repository = consent_repository

    def evaluate(
        self,
        *,
        beneficiary_user_id: str,
        requires_parental_authorization: bool,
    ) -> PaymentAuthorizationDecision:
        if not beneficiary_user_id:
            raise ValueError(
                "beneficiary_user_id cannot be empty."
            )

        if not requires_parental_authorization:
            return PaymentAuthorizationDecision(
                decision=AuthorizationDecision.AUTHORIZED,
                beneficiary_user_id=beneficiary_user_id,
                payer_user_id=beneficiary_user_id,
            )

        relationships = (
            self.relationship_repository
            .get_active_parents_for_child(
                beneficiary_user_id
            )
        )

        if not relationships:
            return PaymentAuthorizationDecision(
                decision=AuthorizationDecision.NO_GUARDIAN,
                beneficiary_user_id=beneficiary_user_id,
            )

        for relationship in relationships:
            parent_user_id = relationship.parent_user_id

            if self.consent_repository.has_active_payment_consent(
                parent_user_id=parent_user_id,
                child_user_id=beneficiary_user_id,
            ):
                return PaymentAuthorizationDecision(
                    decision=AuthorizationDecision.AUTHORIZED,
                    beneficiary_user_id=beneficiary_user_id,
                    payer_user_id=parent_user_id,
                )

        return PaymentAuthorizationDecision(
            decision=AuthorizationDecision.APPROVAL_REQUIRED,
            beneficiary_user_id=beneficiary_user_id,
        )


__all__ = ["PaymentAuthorizationService"]
