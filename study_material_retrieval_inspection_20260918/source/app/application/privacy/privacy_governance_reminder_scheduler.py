from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

from .privacy_governance_reminder_history import (
    PrivacyGovernanceReminderHistory,
)
from .privacy_governance_reminder_policy import (
    GovernanceReminderPolicy,
    build_decision_proposal,
)
from .privacy_governance_reminder_result import (
    PrivacyGovernanceReminderResult,
)


class GovernanceReminderStatePort(Protocol):
    def get_last_sent(self, case_id: str) -> Any:
        ...

    def record(
        self,
        *,
        case_id: str,
        sent_at: datetime,
        recipient_role: str,
        email_reference: str | None = None,
    ) -> Any:
        ...


class GovernanceReminderEmailPort(Protocol):
    def send_reminder(
        self,
        *,
        case: Any,
        proposal: Any,
    ) -> None:
        ...


class PrivacyGovernanceReminderEmailPort(Protocol):
    async def send_governance_reminder(
        self,
        *,
        case: Any,
        recipient_role: str,
        reason: str,
    ) -> Any:
        ...


class InMemoryGovernanceReminderState(
    PrivacyGovernanceReminderHistory
):
    """Process-local Beta reminder state."""

    pass


@dataclass(frozen=True, slots=True)
class GovernanceReminderRunResult:
    """Aggregate result for the operational follow-up invocation."""

    scanned: int
    reminded: int
    case_ids_reminded: tuple[str, ...]


class PrivacyGovernanceCaseRegistryPort(Protocol):
    def all(self) -> tuple[Any, ...]:
        ...

    def get(self, case_id: str) -> Any:
        ...


class PrivacyGovernanceReminderScheduler:
    """Single governance reminder workflow with compatibility contracts.

    Supported application contract:

        run_once()
        reminder_state
        email_sender

    Supported cybersecurity contract:

        run()
        run_case()
        history
        email_service

    This class is not an APScheduler implementation. It is an application
    workflow invoked by the approved scheduler runtime.
    """

    def __init__(
        self,
        *,
        case_registry: Any,
        policy: GovernanceReminderPolicy,
        reminder_state: GovernanceReminderStatePort | None = None,
        email_sender: GovernanceReminderEmailPort | None = None,
        history: PrivacyGovernanceReminderHistory | None = None,
        email_service: PrivacyGovernanceReminderEmailPort | None = None,
    ) -> None:
        if case_registry is None:
            raise ValueError(
                "case_registry cannot be None."
            )

        if policy is None:
            raise ValueError(
                "policy cannot be None."
            )

        self.case_registry = case_registry
        self.policy = policy

        self.reminder_state = (
            reminder_state
            or history
            or InMemoryGovernanceReminderState()
        )

        self.email_sender = email_sender
        self.email_service = email_service

    # ------------------------------------------------------------------
    # Phase 6J operational follow-up API
    # ------------------------------------------------------------------

    def run_once(
        self,
        *,
        now: datetime | None = None,
    ) -> GovernanceReminderRunResult:
        """Run the synchronous operational follow-up contract."""

        current = now or datetime.now(timezone.utc)

        self._validate_now(current)

        cases = tuple(
            self.case_registry.all()
        )

        reminded: list[str] = []

        for case in cases:
            if self._run_sync_case(
                case,
                now=current,
            ):
                reminded.append(
                    case.case_id
                )

        return GovernanceReminderRunResult(
            scanned=len(cases),
            reminded=len(reminded),
            case_ids_reminded=tuple(reminded),
        )

    def _run_sync_case(
        self,
        case: Any,
        *,
        now: datetime,
    ) -> bool:
        if not self.policy.is_due(
            case,
            history=self.reminder_state,
            now=now,
        ):
            return False

        if self.email_sender is None:
            return False

        proposal = build_decision_proposal(case)

        self.email_sender.send_reminder(
            case=case,
            proposal=proposal,
        )

        self.reminder_state.record(
            case_id=case.case_id,
            sent_at=now,
            recipient_role=self.policy.recipient_role,
        )

        return True

    # ------------------------------------------------------------------
    # Existing cybersecurity async API
    # ------------------------------------------------------------------

    async def run(
        self,
        *,
        now: datetime | None = None,
    ) -> tuple[PrivacyGovernanceReminderResult, ...]:
        """Evaluate all cases through the async email-service contract."""

        current = now or datetime.now(timezone.utc)

        self._validate_now(current)

        results: list[
            PrivacyGovernanceReminderResult
        ] = []

        for case in self.case_registry.all():
            results.append(
                await self._evaluate_case(
                    case,
                    now=current,
                )
            )

        return tuple(results)

    async def run_case(
        self,
        case_id: str,
        *,
        now: datetime | None = None,
    ) -> PrivacyGovernanceReminderResult:
        """Evaluate one case through the async contract."""

        current = now or datetime.now(timezone.utc)

        self._validate_now(current)

        case = self.case_registry.get(
            case_id
        )

        return await self._evaluate_case(
            case,
            now=current,
        )

    async def _evaluate_case(
        self,
        case: Any,
        *,
        now: datetime,
    ) -> PrivacyGovernanceReminderResult:
        if not self.policy.is_eligible(case):
            return PrivacyGovernanceReminderResult(
                status="NOT_ELIGIBLE",
                case_id=case.case_id,
                governance_status=case.governance_status,
                due=False,
                recipient_role=self.policy.recipient_role,
                reason="case_not_pending_dpo_grc",
                generated_at=now,
            )

        if not self.policy.is_due(
            case,
            history=self.reminder_state,
            now=now,
        ):
            return PrivacyGovernanceReminderResult(
                status="NOT_DUE",
                case_id=case.case_id,
                governance_status=case.governance_status,
                due=False,
                recipient_role=self.policy.recipient_role,
                reason="reminder_interval_or_cooldown_not_reached",
                generated_at=now,
            )

        reason = (
            "pending_dpo_grc_reminder_due"
        )

        if self.email_service is None:
            return PrivacyGovernanceReminderResult(
                status="DUE",
                case_id=case.case_id,
                governance_status=case.governance_status,
                due=True,
                recipient_role=self.policy.recipient_role,
                reason=reason,
                generated_at=now,
                email_status="not_configured",
            )

        try:
            response = (
                await self.email_service.send_governance_reminder(
                    case=case,
                    recipient_role=self.policy.recipient_role,
                    reason=reason,
                )
            )
        except Exception as exc:
            return PrivacyGovernanceReminderResult(
                status="EMAIL_FAILED",
                case_id=case.case_id,
                governance_status=case.governance_status,
                due=True,
                recipient_role=self.policy.recipient_role,
                reason=reason,
                generated_at=now,
                email_status="failed",
                error=str(exc),
            )

        email_status = "sent"
        reference: str | None = None
        case_url: str | None = None

        if isinstance(response, dict):
            email_status = str(
                response.get(
                    "status",
                    "sent",
                )
            )

            value = (
                response.get("reference")
                or response.get("message_id")
            )

            if value is not None:
                reference = str(value)

            url = response.get("case_url")

            if url is not None:
                case_url = str(url)

        elif response is not None:
            reference = str(response)

        self.reminder_state.record(
            case_id=case.case_id,
            sent_at=now,
            recipient_role=self.policy.recipient_role,
            email_reference=reference,
        )

        return PrivacyGovernanceReminderResult(
            status="REMINDER_SENT",
            case_id=case.case_id,
            governance_status=case.governance_status,
            due=True,
            recipient_role=self.policy.recipient_role,
            reason=reason,
            generated_at=now,
            email_status=email_status,
            email_reference=reference,
            case_url=case_url,
        )

    @staticmethod
    def _validate_now(
        now: datetime,
    ) -> None:
        if now.tzinfo is None:
            raise ValueError(
                "now must be timezone-aware."
            )


__all__ = [
    "GovernanceReminderEmailPort",
    "GovernanceReminderRunResult",
    "GovernanceReminderStatePort",
    "InMemoryGovernanceReminderState",
    "PrivacyGovernanceCaseRegistryPort",
    "PrivacyGovernanceReminderEmailPort",
    "PrivacyGovernanceReminderScheduler",
]