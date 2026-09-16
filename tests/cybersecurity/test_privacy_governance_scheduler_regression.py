from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from app.application.privacy.privacy_governance_reminder_history import (
    PrivacyGovernanceReminderHistory,
)
from app.application.privacy.privacy_governance_reminder_policy import (
    PrivacyGovernanceReminderPolicy,
)
from app.application.privacy.privacy_governance_reminder_scheduler import (
    PrivacyGovernanceReminderScheduler,
)


@dataclass(frozen=True)
class Case:
    case_id: str
    governance_status: str
    triggered_at: datetime
    title: str = "Privacy governance test"
    change_id: str = "PCR-REGRESSION-001"
    risk: str = "MEDIUM"
    validation_status: str = "PASS"


class FakeCaseRegistry:
    def __init__(self, cases: list[Case]) -> None:
        self._cases = tuple(cases)

    def all(self) -> tuple[Case, ...]:
        return self._cases

    def get(self, case_id: str) -> Case:
        for case in self._cases:
            if case.case_id == case_id:
                return case
        raise KeyError(f"Governance case not found: {case_id}")


class FakeEmailService:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.fail = False

    async def send_governance_reminder(
        self,
        *,
        case: Case,
        recipient_role: str,
        reason: str,
    ) -> dict[str, object]:
        del recipient_role, reason

        if self.fail:
            raise RuntimeError("Simulated email delivery failure.")

        self.calls.append(case.case_id)

        return {
            "status": "sent",
            "reference": f"MSG-{len(self.calls):03d}",
            "case_url": (
                "http://127.0.0.1:5173/privacy-governance/"
                f"{case.case_id}"
            ),
        }


def make_scheduler(
    cases: list[Case],
    *,
    email: FakeEmailService | None = None,
) -> tuple[PrivacyGovernanceReminderScheduler, FakeEmailService]:
    email_service = email or FakeEmailService()

    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=FakeCaseRegistry(cases),
        policy=PrivacyGovernanceReminderPolicy(
            reminder_after=timedelta(hours=24),
            cooldown=timedelta(hours=24),
        ),
        history=PrivacyGovernanceReminderHistory(),
        email_service=email_service,
    )

    return scheduler, email_service


@pytest.mark.asyncio
async def test_pending_case_reminder_is_sent_and_contains_case_url() -> None:
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    case = Case(
        case_id="CASE-REG-001",
        governance_status="PENDING_DPO_GRC",
        triggered_at=now - timedelta(hours=25),
    )

    scheduler, email = make_scheduler([case])

    results = await scheduler.run(now=now)

    assert len(results) == 1
    assert results[0].status == "REMINDER_SENT"
    assert results[0].email_status == "sent"
    assert results[0].case_url == (
        "http://127.0.0.1:5173/privacy-governance/CASE-REG-001"
    )
    assert email.calls == ["CASE-REG-001"]


@pytest.mark.asyncio
async def test_approved_case_does_not_receive_reminder() -> None:
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    case = Case(
        case_id="CASE-REG-APPROVED",
        governance_status="APPROVED",
        triggered_at=now - timedelta(days=7),
    )

    scheduler, email = make_scheduler([case])

    results = await scheduler.run(now=now)

    assert results[0].status == "NOT_ELIGIBLE"
    assert results[0].governance_status == "APPROVED"
    assert email.calls == []


@pytest.mark.asyncio
async def test_blocked_case_does_not_receive_reminder() -> None:
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    case = Case(
        case_id="CASE-REG-BLOCKED",
        governance_status="BLOCKED",
        triggered_at=now - timedelta(days=7),
    )

    scheduler, email = make_scheduler([case])

    results = await scheduler.run(now=now)

    assert results[0].status == "NOT_ELIGIBLE"
    assert results[0].governance_status == "BLOCKED"
    assert email.calls == []


@pytest.mark.asyncio
async def test_cooldown_prevents_repeated_reminder() -> None:
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    case = Case(
        case_id="CASE-REG-COOLDOWN",
        governance_status="PENDING_DPO_GRC",
        triggered_at=now - timedelta(hours=48),
    )

    scheduler, email = make_scheduler([case])

    first = await scheduler.run(now=now)
    second = await scheduler.run(now=now + timedelta(hours=1))

    assert first[0].status == "REMINDER_SENT"
    assert second[0].status == "NOT_DUE"
    assert email.calls == ["CASE-REG-COOLDOWN"]


@pytest.mark.asyncio
async def test_email_failure_does_not_crash_scheduler() -> None:
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    case = Case(
        case_id="CASE-REG-EMAIL-FAIL",
        governance_status="PENDING_DPO_GRC",
        triggered_at=now - timedelta(hours=25),
    )

    email = FakeEmailService()
    email.fail = True

    scheduler, _ = make_scheduler([case], email=email)

    results = await scheduler.run(now=now)

    assert results[0].status == "EMAIL_FAILED"
    assert results[0].email_status == "failed"
    assert results[0].error == "Simulated email delivery failure."
    assert email.calls == []


@pytest.mark.asyncio
async def test_mixed_cases_only_pending_due_case_is_notified() -> None:
    now = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)

    cases = [
        Case(
            case_id="CASE-REG-PENDING",
            governance_status="PENDING_DPO_GRC",
            triggered_at=now - timedelta(hours=25),
        ),
        Case(
            case_id="CASE-REG-APPROVED",
            governance_status="APPROVED",
            triggered_at=now - timedelta(days=3),
        ),
        Case(
            case_id="CASE-REG-BLOCKED",
            governance_status="BLOCKED",
            triggered_at=now - timedelta(days=3),
        ),
    ]

    scheduler, email = make_scheduler(cases)

    results = await scheduler.run(now=now)

    assert [result.status for result in results] == [
        "REMINDER_SENT",
        "NOT_ELIGIBLE",
        "NOT_ELIGIBLE",
    ]
    assert email.calls == ["CASE-REG-PENDING"]
