from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .privacy_governance_reminder_history import (
    PrivacyGovernanceReminderHistory,
)


@dataclass(frozen=True, slots=True)
class GovernanceDecisionProposal:
    """Human-review decision support.

    This object presents the available governance actions. It never makes
    or applies a governance decision.
    """

    case_id: str
    change_id: str | None
    title: str
    risk: str
    validation_status: str
    governance_status: str
    required_roles: tuple[str, ...]
    decision_options: tuple[str, ...] = (
        "APPROVE",
        "REJECT",
        "REQUEST_CHANGES",
    )

    @property
    def summary(self) -> str:
        change = self.change_id or "NOT_LINKED"
        roles = ", ".join(self.required_roles) or "DPO/GRC"

        return (
            f"Case {self.case_id} concerns change {change}. "
            f"Risk: {self.risk}. Automated validation: "
            f"{self.validation_status}. Current governance status: "
            f"{self.governance_status}. Required reviewer role(s): {roles}. "
            "No decision is made by the scheduler; the reviewer must assess "
            "the underlying evidence and explicitly record APPROVE, REJECT, "
            "or REQUEST_CHANGES."
        )


@dataclass(slots=True)
class GovernanceReminderPolicy:
    """Canonical Phase 6J governance reminder policy.

    Only PENDING_DPO_GRC cases are eligible.

    ``repeat_after`` is the canonical Phase 6J.1 name.

    ``cooldown`` is retained as a backwards-compatible constructor alias
    because existing cybersecurity tests and integrations use that name.
    """

    reminder_after: timedelta = timedelta(hours=24)
    repeat_after: timedelta | None = None
    cooldown: timedelta | None = None
    recipient_role: str = "DPO/GRC"

    def __post_init__(self) -> None:
        if self.repeat_after is not None and self.cooldown is not None:
            if self.repeat_after != self.cooldown:
                raise ValueError(
                    "repeat_after and cooldown must match when both are supplied."
                )

        resolved_repeat = (
            self.repeat_after
            if self.repeat_after is not None
            else self.cooldown
        )

        if resolved_repeat is None:
            resolved_repeat = timedelta(hours=24)

        self.repeat_after = resolved_repeat
        self.cooldown = resolved_repeat

        if self.reminder_after.total_seconds() < 0:
            raise ValueError(
                "reminder_after cannot be negative."
            )

        if resolved_repeat.total_seconds() < 0:
            raise ValueError(
                "repeat_after cannot be negative."
            )

        if not self.recipient_role.strip():
            raise ValueError(
                "recipient_role is required."
            )

    def is_eligible(self, case: Any) -> bool:
        """Return whether the case is awaiting human governance."""

        return (
            getattr(case, "governance_status", None)
            == "PENDING_DPO_GRC"
        )

    def due_at(self, case: Any) -> datetime:
        """Return the first reminder due time."""

        triggered_at = getattr(
            case,
            "triggered_at",
            None,
        )

        if not isinstance(triggered_at, datetime):
            raise ValueError(
                "case.triggered_at must be a datetime."
            )

        if triggered_at.tzinfo is None:
            raise ValueError(
                "case.triggered_at must be timezone-aware."
            )

        return triggered_at + self.reminder_after

    def is_due(
        self,
        case: Any,
        *,
        history: PrivacyGovernanceReminderHistory | None = None,
        now: datetime | None = None,
        last_sent_at: datetime | None = None,
    ) -> bool:
        """Return whether a reminder is due.

        ``history`` is the canonical state adapter.

        ``last_sent_at`` is retained for compatibility with older policy
        callers.
        """

        if not self.is_eligible(case):
            return False

        current = now or datetime.now(timezone.utc)

        if current.tzinfo is None:
            raise ValueError(
                "now must be timezone-aware."
            )

        if last_sent_at is None and history is not None:
            previous = history.get_last_sent(case.case_id)
            if previous is not None:
                last_sent_at = previous.sent_at

        if current < self.due_at(case):
            return False

        if last_sent_at is None:
            return True

        if last_sent_at.tzinfo is None:
            raise ValueError(
                "last_sent_at must be timezone-aware."
            )

        return current >= (
            last_sent_at + self.repeat_after
        )


def build_decision_proposal(
    case: Any,
) -> GovernanceDecisionProposal:
    """Build non-binding human governance decision support."""

    dpo_required = bool(
        getattr(case, "dpo_required", True)
    )
    grc_required = bool(
        getattr(case, "grc_required", True)
    )

    required_roles = tuple(
        role
        for role, required in (
            ("DPO", dpo_required),
            ("GRC", grc_required),
        )
        if required
    )

    return GovernanceDecisionProposal(
        case_id=case.case_id,
        change_id=getattr(case, "change_id", None),
        title=str(getattr(case, "title", "")),
        risk=str(getattr(case, "risk", "UNKNOWN")),
        validation_status=str(
            getattr(
                case,
                "validation_status",
                "UNKNOWN",
            )
        ),
        governance_status=str(
            getattr(
                case,
                "governance_status",
                "UNKNOWN",
            )
        ),
        required_roles=required_roles,
    )


PrivacyGovernanceReminderPolicy = GovernanceReminderPolicy


__all__ = [
    "GovernanceDecisionProposal",
    "GovernanceReminderPolicy",
    "PrivacyGovernanceReminderPolicy",
    "build_decision_proposal",
]