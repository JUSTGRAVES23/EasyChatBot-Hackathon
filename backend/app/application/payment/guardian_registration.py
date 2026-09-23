from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RegistrationPolicyClassification(str, Enum):
    """
    Product-neutral registration policy classifications.

    These classifications are intentionally separated from payment and
    Stripe concepts. The policy layer decides whether guardian involvement
    is required; the payment layer consumes that decision.
    """

    ADULT = "adult"
    MINOR = "minor"
    STUDENT = "student"


@dataclass(frozen=True)
class GuardianRegistrationRequirement:
    """
    Result of registration-policy evaluation.

    guardian_required is the authoritative decision consumed by onboarding
    and, where applicable, family/payment authorization flows.
    """

    guardian_required: bool
    guardian_email: str | None = None
    policy_classification: RegistrationPolicyClassification | None = None

    @property
    def required(self) -> bool:
        """
        Backward-compatible read-only alias for the previous contract.
        """
        return self.guardian_required


def evaluate_guardian_registration_requirement(
    classification: RegistrationPolicyClassification,
    guardian_email: str | None = None,
    *,
    guardian_required: bool = False,
) -> GuardianRegistrationRequirement:
    """
    Evaluate whether guardian registration is required.

    The decision is explicit rather than deriving legal meaning from a
    hard-coded age bucket such as UNDER_15.

    Age/jurisdiction policy can determine guardian_required upstream.
    This function remains reusable by the P5B family/payment flow.
    """

    normalized_email = (
        guardian_email.strip().lower()
        if guardian_email and guardian_email.strip()
        else None
    )

    if guardian_required:
        return GuardianRegistrationRequirement(
            guardian_required=True,
            guardian_email=normalized_email,
            policy_classification=classification,
        )

    return GuardianRegistrationRequirement(
        guardian_required=False,
        guardian_email=None,
        policy_classification=classification,
    )


__all__ = [
    "RegistrationPolicyClassification",
    "GuardianRegistrationRequirement",
    "evaluate_guardian_registration_requirement",
]