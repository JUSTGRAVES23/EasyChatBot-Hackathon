from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ApprovalDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUEST_CHANGES = "REQUEST_CHANGES"


@dataclass(frozen=True, slots=True)
class PrivacyApprovalRecord:
    """Immutable, auditable human governance decision."""

    approval_id: str
    case_id: str
    change_id: str
    reviewer: str
    role: str
    decision: ApprovalDecision
    comment: str
    decided_at: datetime

    def __post_init__(self) -> None:
        for field_name in (
            "approval_id",
            "case_id",
            "change_id",
            "reviewer",
            "role",
            "comment",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} is required.")
        if self.role.upper() not in {"DPO", "GRC"}:
            raise ValueError("role must be DPO or GRC.")
        if self.decided_at.tzinfo is None:
            raise ValueError("decided_at must be timezone-aware.")
