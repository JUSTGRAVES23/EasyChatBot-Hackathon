from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from backend.app.application.privacy.privacy_governance_reminder_history import (
    PrivacyGovernanceReminderHistory,
)
from backend.app.application.privacy.privacy_governance_reminder_policy import (
    PrivacyGovernanceReminderPolicy,
)
from backend.app.application.privacy.privacy_governance_reminder_scheduler import (
    PrivacyGovernanceReminderScheduler,
)


@dataclass(frozen=True)
class Case:
    case_id: str
    governance_status: str
    triggered_at: datetime
    title: str = "New learner data processing"
    change_id: str = "PCR-001"
    risk: str = "MEDIUM"
    validation_status: str = "PASS"


class FakeRegistry:
    def __init__(self, cases):
        self._cases = tuple(cases)

    def all(self):
        return self._cases

    def get(self, case_id):
        return next(c for c in self._cases if c.case_id == case_id)


class FakeEmail:
    def __init__(self):
        self.calls = 0

    async def send_governance_reminder(self, **kwargs):
        self.calls += 1
        return {
            "status": "sent",
            "reference": f"MSG-{self.calls}",
            "case_url": (
                "http://127.0.0.1:5173/privacy-governance/"
                f"{kwargs['case'].case_id}"
            ),
        }


@pytest.mark.asyncio
async def test_due_pending_case_sends_once_within_cooldown():
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)
    case = Case(
        case_id="CASE-001",
        governance_status="PENDING_DPO_GRC",
        triggered_at=now - timedelta(hours=25),
    )
    email = FakeEmail()

    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=FakeRegistry([case]),
        policy=PrivacyGovernanceReminderPolicy(
            reminder_after=timedelta(hours=24),
            cooldown=timedelta(hours=24),
        ),
        history=PrivacyGovernanceReminderHistory(),
        email_service=email,
    )

    first = await scheduler.run(now=now)
    second = await scheduler.run(
        now=now + timedelta(hours=1),
    )

    assert first[0].status == "REMINDER_SENT"
    assert second[0].status == "NOT_DUE"
    assert email.calls == 1


@pytest.mark.asyncio
async def test_approved_case_never_sends():
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)
    case = Case(
        case_id="CASE-APPROVED",
        governance_status="APPROVED",
        triggered_at=now - timedelta(days=5),
    )
    email = FakeEmail()

    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=FakeRegistry([case]),
        policy=PrivacyGovernanceReminderPolicy(
            reminder_after=timedelta(),
        ),
        history=PrivacyGovernanceReminderHistory(),
        email_service=email,
    )

    result = await scheduler.run(now=now)

    assert result[0].status == "NOT_ELIGIBLE"
    assert email.calls == 0


@pytest.mark.asyncio
async def test_blocked_case_never_sends():
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)
    case = Case(
        case_id="CASE-BLOCKED",
        governance_status="BLOCKED",
        triggered_at=now - timedelta(days=5),
    )
    email = FakeEmail()

    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=FakeRegistry([case]),
        policy=PrivacyGovernanceReminderPolicy(
            reminder_after=timedelta(),
        ),
        history=PrivacyGovernanceReminderHistory(),
        email_service=email,
    )

    result = await scheduler.run(now=now)

    assert result[0].status == "NOT_ELIGIBLE"
    assert email.calls == 0
