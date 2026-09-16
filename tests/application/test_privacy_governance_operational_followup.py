from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.application.privacy.privacy_governance_operational_followup import (
    create_privacy_governance_operational_follow_up,
)
from app.application.privacy.privacy_governance_reminder_policy import (
    GovernanceReminderPolicy,
)
from app.application.privacy.privacy_governance_reminder_scheduler import (
    InMemoryGovernanceReminderState,
)


@dataclass(frozen=True)
class Case:
    case_id: str
    change_id: str
    title: str
    risk: str
    validation_status: str
    governance_status: str
    triggered_at: datetime
    dpo_required: bool = True
    grc_required: bool = True


class Registry:
    def __init__(self, cases):
        self._cases = list(cases)

    def all(self):
        return list(self._cases)


class FakeEmail:
    def __init__(self):
        self.sent = []

    def send_reminder(self, *, case, proposal):
        self.sent.append((case, proposal))


def make_case(status: str = "PENDING_DPO_GRC") -> Case:
    return Case(
        case_id="CASE-6J-OPS-001",
        change_id="PCR-6J-OPS-001",
        title="Operational follow-up test",
        risk="MEDIUM",
        validation_status="PASS",
        governance_status=status,
        triggered_at=datetime(
            2026, 8, 22, 10, 0, tzinfo=timezone.utc
        ),
    )


def test_existing_scheduler_can_invoke_operational_followup():
    email = FakeEmail()
    job = create_privacy_governance_operational_follow_up(
        case_registry=Registry([make_case()]),
        reminder_state=InMemoryGovernanceReminderState(),
        email_sender=email,
        policy=GovernanceReminderPolicy(
            reminder_after=timedelta(hours=24),
            repeat_after=timedelta(hours=24),
        ),
    )

    result = job.run_once(
        now=datetime(2026, 8, 23, 11, 0, tzinfo=timezone.utc)
    )

    assert result.scanned == 1
    assert result.reminded == 1
    assert result.case_ids_reminded == ("CASE-6J-OPS-001",)
    assert len(email.sent) == 1


def test_followup_does_not_make_a_governance_decision():
    case = make_case()
    email = FakeEmail()
    job = create_privacy_governance_operational_follow_up(
        case_registry=Registry([case]),
        reminder_state=InMemoryGovernanceReminderState(),
        email_sender=email,
    )

    job.run_once(
        now=datetime(2026, 8, 23, 11, 0, tzinfo=timezone.utc)
    )

    assert case.governance_status == "PENDING_DPO_GRC"
    assert email.sent[0][1].decision_options == (
        "APPROVE",
        "REJECT",
        "REQUEST_CHANGES",
    )


def test_terminal_cases_are_not_followed_up():
    email = FakeEmail()
    job = create_privacy_governance_operational_follow_up(
        case_registry=Registry([
            make_case("APPROVED"),
            make_case("BLOCKED"),
        ]),
        reminder_state=InMemoryGovernanceReminderState(),
        email_sender=email,
        policy=GovernanceReminderPolicy(
            reminder_after=timedelta(hours=1),
        ),
    )

    result = job.run_once(
        now=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    )

    assert result.scanned == 2
    assert result.reminded == 0
    assert email.sent == []


def test_second_scheduler_invocation_is_idempotent_within_beta_state():
    email = FakeEmail()
    state = InMemoryGovernanceReminderState()
    job = create_privacy_governance_operational_follow_up(
        case_registry=Registry([make_case()]),
        reminder_state=state,
        email_sender=email,
        policy=GovernanceReminderPolicy(
            reminder_after=timedelta(hours=24),
            repeat_after=timedelta(hours=24),
        ),
    )

    first = job.run_once(
        now=datetime(2026, 8, 23, 11, 0, tzinfo=timezone.utc)
    )
    second = job.run_once(
        now=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    )

    assert first.reminded == 1
    assert second.reminded == 0
    assert len(email.sent) == 1


def test_job_is_read_only_against_case_registry():
    case = make_case()
    email = FakeEmail()
    job = create_privacy_governance_operational_follow_up(
        case_registry=Registry([case]),
        reminder_state=InMemoryGovernanceReminderState(),
        email_sender=email,
        policy=GovernanceReminderPolicy(
            reminder_after=timedelta(hours=1),
        ),
    )

    job.run_once(
        now=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc)
    )

    assert case.governance_status == "PENDING_DPO_GRC"
    assert case.change_id == "PCR-6J-OPS-001"

