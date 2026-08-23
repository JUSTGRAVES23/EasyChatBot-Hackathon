from __future__ import annotations

from datetime import datetime, timezone

from backend.app.application.privacy.privacy_governance_reminder_history import (
    PrivacyGovernanceReminderHistory,
)


def test_history_records_last_reminder():
    history = PrivacyGovernanceReminderHistory()
    sent_at = datetime.now(timezone.utc)

    record = history.record(
        case_id="CASE-001",
        sent_at=sent_at,
        recipient_role="DPO/GRC",
        email_reference="MSG-001",
    )

    assert history.get_last_sent("CASE-001") == record
