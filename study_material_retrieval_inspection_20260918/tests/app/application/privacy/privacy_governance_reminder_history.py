from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PrivacyGovernanceReminderRecord:
    case_id: str
    sent_at: datetime
    recipient_role: str
    email_reference: str | None = None


class PrivacyGovernanceReminderHistory:
    """Replaceable reminder history used for cooldown protection.

    The Beta implementation is process-local. The interface is intentionally
    isolated so persistent storage can be introduced later without changing
    the scheduler workflow.
    """

    def __init__(self) -> None:
        self._records: dict[str, PrivacyGovernanceReminderRecord] = {}

    def get_last_sent(
        self,
        case_id: str,
    ) -> PrivacyGovernanceReminderRecord | None:
        return self._records.get(case_id)

    def record(
        self,
        *,
        case_id: str,
        sent_at: datetime,
        recipient_role: str,
        email_reference: str | None = None,
    ) -> PrivacyGovernanceReminderRecord:
        if not case_id.strip():
            raise ValueError("case_id is required.")
        if sent_at.tzinfo is None:
            raise ValueError("sent_at must be timezone-aware.")

        record = PrivacyGovernanceReminderRecord(
            case_id=case_id,
            sent_at=sent_at,
            recipient_role=recipient_role,
            email_reference=email_reference,
        )
        self._records[case_id] = record
        return record


__all__ = [
    "PrivacyGovernanceReminderHistory",
    "PrivacyGovernanceReminderRecord",
]
