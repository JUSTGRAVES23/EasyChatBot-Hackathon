from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthorizationDecision(str, Enum):
    AUTHORIZED = "authorized"
    APPROVAL_REQUIRED = "approval_required"
    NO_GUARDIAN = "no_guardian"
    CONSENT_REQUIRED = "consent_required"
    NOT_AUTHORIZED = "not_authorized"


@dataclass(frozen=True)
class PaymentAuthorizationDecision:
    decision: AuthorizationDecision
    beneficiary_user_id: str
    payer_user_id: str | None = None


__all__ = [
    "AuthorizationDecision",
    "PaymentAuthorizationDecision",
]
