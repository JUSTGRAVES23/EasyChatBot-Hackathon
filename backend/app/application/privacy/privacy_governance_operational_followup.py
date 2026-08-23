from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .privacy_governance_reminder_policy import (
    GovernanceReminderPolicy,
)
from .privacy_governance_reminder_scheduler import (
    GovernanceReminderRunResult,
    GovernanceReminderStatePort,
    GovernanceReminderEmailPort,
    PrivacyGovernanceReminderScheduler,
)


class GovernanceCaseRegistryPort(Protocol):
    """Read-only registry contract required by the operational follow-up job."""

    def all(self) -> list[object]:
        ...


class GovernanceOperationalFollowUpJob(Protocol):
    """Contract suitable for registration with the existing scheduler runtime."""

    def run_once(self, *, now: datetime | None = None) -> GovernanceReminderRunResult:
        ...


@dataclass(slots=True)
class PrivacyGovernanceOperationalFollowUp:
    """Controlled operational entry point for governance follow-up.

    This is deliberately an application job, not a second scheduler framework.
    The existing platform scheduler should invoke ``run_once`` at its approved
    cadence. The governance policy decides whether an individual case is due.

    The job:
    - reads governance cases;
    - evaluates the existing reminder policy;
    - sends controlled decision-support reminders;
    - records reminder evidence/idempotency state.

    It MUST NOT approve, reject, request changes, or mutate governance state.
    """

    scheduler: PrivacyGovernanceReminderScheduler

    def run_once(
        self,
        *,
        now: datetime | None = None,
    ) -> GovernanceReminderRunResult:
        return self.scheduler.run_once(now=now)


def create_privacy_governance_operational_follow_up(
    *,
    case_registry: GovernanceCaseRegistryPort,
    reminder_state: GovernanceReminderStatePort,
    email_sender: GovernanceReminderEmailPort,
    policy: GovernanceReminderPolicy | None = None,
) -> PrivacyGovernanceOperationalFollowUp:
    """Build the governance follow-up job using existing scheduler infrastructure.

    The caller owns the lifecycle of the state and email adapters. In
    production, ``reminder_state`` should be persistent and idempotent.
    """

    if case_registry is None:
        raise ValueError("case_registry cannot be None.")
    if reminder_state is None:
        raise ValueError("reminder_state cannot be None.")
    if email_sender is None:
        raise ValueError("email_sender cannot be None.")

    scheduler = PrivacyGovernanceReminderScheduler(
        case_registry=case_registry,
        policy=policy or GovernanceReminderPolicy(),
        reminder_state=reminder_state,
        email_sender=email_sender,
    )
    return PrivacyGovernanceOperationalFollowUp(scheduler=scheduler)


__all__ = [
    "GovernanceCaseRegistryPort",
    "GovernanceOperationalFollowUpJob",
    "PrivacyGovernanceOperationalFollowUp",
    "create_privacy_governance_operational_follow_up",
]
