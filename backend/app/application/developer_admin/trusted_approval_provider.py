from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.identity.authentication_assurance import AuthenticationAssuranceContext
from app.domain.identity.transaction_authorization import TrustedApprovalEvidence


class TrustedApprovalUnavailableError(RuntimeError):
    """No trusted MFA/WebAuthn/IAM approval provider is configured."""


@dataclass(frozen=True, slots=True)
class TrustedApprovalRequest:
    """Provider-neutral request for approval of one exact transaction."""

    authorization_id: str
    principal_id: str
    audience: str
    transaction_id: str
    requested_at: datetime


class TrustedApprovalProvider(Protocol):
    """Port for a trusted MFA/WebAuthn/IAM approval boundary."""

    async def approve(
        self,
        *,
        request: TrustedApprovalRequest,
    ) -> TrustedApprovalEvidence:
        """Return trusted evidence or raise on denial/unavailability."""
        ...


class UnavailableTrustedApprovalProvider:
    """Production-safe default until a real trusted provider is configured."""

    async def approve(
        self,
        *,
        request: TrustedApprovalRequest,
    ) -> TrustedApprovalEvidence:
        raise TrustedApprovalUnavailableError(
            "Trusted A2 approval provider is not configured."
        )


__all__ = [
    "TrustedApprovalRequest",
    "TrustedApprovalProvider",
    "TrustedApprovalUnavailableError",
    "UnavailableTrustedApprovalProvider",
]
