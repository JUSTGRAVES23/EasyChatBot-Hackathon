from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PrivacyGovernanceReminderResult:
    status: str
    case_id: str
    governance_status: str
    due: bool
    recipient_role: str
    reason: str
    generated_at: datetime
    email_status: str | None = None
    email_reference: str | None = None
    case_url: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "case_id": self.case_id,
            "governance_status": self.governance_status,
            "due": self.due,
            "recipient_role": self.recipient_role,
            "reason": self.reason,
            "generated_at": self.generated_at.isoformat(),
            "email_status": self.email_status,
            "email_reference": self.email_reference,
            "case_url": self.case_url,
            "error": self.error,
        }


__all__ = ["PrivacyGovernanceReminderResult"]
