"""Contracts for controlled PI escalation retry candidate claiming."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RetryCandidateClaimStatus(StrEnum):
    CLAIMED = "CLAIMED"
    NOT_CLAIMED = "NOT_CLAIMED"


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationRetryClaim:
    notification_key: str
    claim_token: str
    claimed_at: datetime
    lease_expires_at: datetime
    status: RetryCandidateClaimStatus = RetryCandidateClaimStatus.CLAIMED

    def __post_init__(self) -> None:
        for field_name in (
            "notification_key",
            "claim_token",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be nonblank.")

        if self.claimed_at.tzinfo is None or self.claimed_at.utcoffset() is None:
            raise ValueError("claimed_at must be timezone-aware.")

        if (
            self.lease_expires_at.tzinfo is None
            or self.lease_expires_at.utcoffset() is None
        ):
            raise ValueError("lease_expires_at must be timezone-aware.")

        if self.lease_expires_at <= self.claimed_at:
            raise ValueError("lease_expires_at must be after claimed_at.")
