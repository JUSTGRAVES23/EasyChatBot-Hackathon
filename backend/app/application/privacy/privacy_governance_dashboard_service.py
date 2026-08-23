from __future__ import annotations

from .privacy_approval_registry import PrivacyApprovalRegistry
from .privacy_governance_case_registry import PrivacyGovernanceCaseRegistry


class PrivacyGovernanceDashboardService:
    """Read-only view model for the EasyChatBot Governance Operations Center.

    This service exposes governance information for the Operations Center.

    It does NOT:
    - approve cases;
    - reject cases;
    - send emails;
    - modify governance state.

    The governance registries remain authoritative. This service only creates
    read-only projections for the API/UI.
    """

    def __init__(
        self,
        *,
        case_registry: PrivacyGovernanceCaseRegistry,
        approval_registry: PrivacyApprovalRegistry,
    ) -> None:
        if case_registry is None:
            raise ValueError("case_registry cannot be None.")

        if approval_registry is None:
            raise ValueError("approval_registry cannot be None.")

        self._cases = case_registry
        self._approvals = approval_registry

    def summary(self) -> dict[str, int]:
        """Return dashboard KPI counts."""

        cases = self._cases.all()

        return {
            "total_cases": len(cases),
            "pending": sum(
                case.governance_status == "PENDING_DPO_GRC"
                for case in cases
            ),
            "approved": sum(
                case.governance_status == "APPROVED"
                for case in cases
            ),
            "blocked": sum(
                case.governance_status == "BLOCKED"
                for case in cases
            ),
            "approval_records": len(
                self._approvals.all()
            ),
        }

    def status_chart(
        self,
    ) -> tuple[dict[str, object], ...]:
        """Return chart-ready governance status counts."""

        summary = self.summary()

        return (
            {
                "status": "Pending DPO/GRC",
                "count": summary["pending"],
            },
            {
                "status": "Approved",
                "count": summary["approved"],
            },
            {
                "status": "Rejected / Blocked",
                "count": summary["blocked"],
            },
        )

    def case_list(
        self,
    ) -> tuple[dict[str, object], ...]:
        """Return clickable governance case rows.

        ``case_id`` is the stable navigation identifier for the UI.

        ``change_id`` is deliberately included so the dashboard preserves
        traceability between the governance case and its authoritative
        PrivacyChange.
        """

        return tuple(
            {
                "case_id": case.case_id,
                "change_id": case.change_id,
                "title": case.title,
                "summary": case.summary,
                "trigger_type": case.trigger_type.value,
                "triggered_at": case.triggered_at.isoformat(),
                "risk": case.risk,
                "validation_status": case.validation_status,
                "email_status": case.email_status,
                "governance_status": case.governance_status,
                "final_decision": case.final_decision,
                "final_decision_at": (
                    case.final_decision_at.isoformat()
                    if case.final_decision_at
                    else None
                ),
            }
            for case in self._cases.all()
        )

    def case_detail(
        self,
        case_id: str,
    ) -> dict[str, object]:
        """Return complete read-only detail for a governance case.

        The ``change_id`` relationship is part of the authoritative case
        traceability chain and must therefore be exposed to the UI.

        A governance decision must never be approved against an untraceable
        case. The decision service remains responsible for enforcing the
        actual governance rule; this service only exposes the relationship.
        """

        case = self._cases.get(case_id)

        records = self._approvals.for_case(case_id)

        return {
            "case_id": case.case_id,
            "change_id": case.change_id,
            "title": case.title,
            "summary": case.summary,
            "trigger": {
                "type": case.trigger_type.value,
                "at": case.triggered_at.isoformat(),
                "source": case.trigger_source,
            },
            "risk": case.risk,
            "processing_ids": list(case.processing_ids),
            "data_map_ids": list(case.data_map_ids),
            "validation_status": case.validation_status,
            "email_status": case.email_status,
            "governance_status": case.governance_status,
            "final_decision": case.final_decision,
            "final_decision_at": (
                case.final_decision_at.isoformat()
                if case.final_decision_at
                else None
            ),
            "approval_history": [
                {
                    "approval_id": record.approval_id,
                    "change_id": record.change_id,
                    "reviewer": record.reviewer,
                    "role": record.role,
                    "decision": record.decision.value,
                    "comment": record.comment,
                    "decided_at": record.decided_at.isoformat(),
                }
                for record in records
            ],
        }


__all__ = ["PrivacyGovernanceDashboardService"]