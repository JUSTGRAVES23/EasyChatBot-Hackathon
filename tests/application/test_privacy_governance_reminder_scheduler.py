from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.app.application.privacy.privacy_governance_reminder_policy import (
    GovernanceReminderPolicy,
    build_decision_proposal,
)
from backend.app.application.privacy.privacy_governance_reminder_scheduler import (
    InMemoryGovernanceReminderState,
    PrivacyGovernanceReminderScheduler,
)


@dataclass(frozen=True)
class Case:
    case_id: str
    change_id: str | None
    title: str
    risk: str
    validation_status: str
    governance_status: str
    triggered_at: datetime
    dpo_required: bool = True
    grc_required: bool = True


class FakeEmail:
    def __init__(self) -> None:
        self.sent = []

    def send_reminder(self, *, case, proposal) -> None:
        self.sent.append((case, proposal))


def make_case(status: str = "PENDING_DPO_GRC") -> Case:
    return Case(
        case_id="CASE-6J-001",
        change_id="PCR-6J-001",
        title="Learner processing change",
        risk="HIGH",
        validation_status="PASS",
        governance_status=status,
        triggered_at=datetime(2026, 8, 22, 10, 0, tzinfo=timezone.utc),
    )


def test_overdue_pending_case_sends_one_reminder():
    case = make_case()
    email = FakeEmail()
    state = InMemoryGovernanceReminderState()
    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=type("Registry", (), {"all": lambda self: [case]})(),
        policy=GovernanceReminderPolicy(reminder_after=timedelta(hours=24)),
        reminder_state=state,
        email_sender=email,
    )

    result = scheduler.run_once(
        now=datetime(2026, 8, 23, 11, 0, tzinfo=timezone.utc)
    )

    assert result.reminded == 1
    assert result.case_ids_reminded == ("CASE-6J-001",)
    assert len(email.sent) == 1
    assert email.sent[0][1].decision_options == (
        "APPROVE", "REJECT", "REQUEST_CHANGES"
    )


def test_non_overdue_case_does_not_send():
    case = make_case()
    email = FakeEmail()
    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=type("Registry", (), {"all": lambda self: [case]})(),
        policy=GovernanceReminderPolicy(reminder_after=timedelta(hours=24)),
        reminder_state=InMemoryGovernanceReminderState(),
        email_sender=email,
    )

    result = scheduler.run_once(
        now=datetime(2026, 8, 23, 9, 59, tzinfo=timezone.utc)
    )

    assert result.reminded == 0
    assert email.sent == []


def test_terminal_case_does_not_send():
    case = make_case("APPROVED")
    email = FakeEmail()
    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=type("Registry", (), {"all": lambda self: [case]})(),
        policy=GovernanceReminderPolicy(reminder_after=timedelta(hours=1)),
        reminder_state=InMemoryGovernanceReminderState(),
        email_sender=email,
    )

    result = scheduler.run_once(
        now=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    )

    assert result.reminded == 0
    assert email.sent == []


def test_repeated_run_is_suppressed_until_repeat_window():
    case = make_case()
    email = FakeEmail()
    state = InMemoryGovernanceReminderState()
    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=type("Registry", (), {"all": lambda self: [case]})(),
        policy=GovernanceReminderPolicy(
            reminder_after=timedelta(hours=24),
            repeat_after=timedelta(hours=24),
        ),
        reminder_state=state,
        email_sender=email,
    )

    first = scheduler.run_once(
        now=datetime(2026, 8, 23, 11, 0, tzinfo=timezone.utc)
    )
    second = scheduler.run_once(
        now=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    )

    assert first.reminded == 1
    assert second.reminded == 0
    assert len(email.sent) == 1


def test_decision_proposal_is_not_an_automatic_decision():
    proposal = build_decision_proposal(make_case())
    assert proposal.governance_status == "PENDING_DPO_GRC"
    assert proposal.decision_options == (
        "APPROVE", "REJECT", "REQUEST_CHANGES"
    )
    assert "No decision is made by the scheduler" in proposal.summary
