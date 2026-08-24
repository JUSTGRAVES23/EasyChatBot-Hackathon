from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from .privacy_approval_record import ApprovalDecision, PrivacyApprovalRecord
from .privacy_approval_registry import PrivacyApprovalRegistry
from .privacy_change import PrivacyChangeStatus
from .privacy_change_registry import PrivacyChangeRegistry
from .privacy_governance_case_registry import PrivacyGovernanceCaseRegistry


class PrivacyGovernanceDecisionService:
    """Records explicit DPO/GRC decisions and updates the governance case."""

    def __init__(
        self,
        *,
        approval_registry: PrivacyApprovalRegistry,
        change_registry: PrivacyChangeRegistry,
        case_registry: PrivacyGovernanceCaseRegistry,
    ) -> None:
        if approval_registry is None:
            raise ValueError("approval_registry cannot be None.")
        if change_registry is None:
            raise ValueError("change_registry cannot be None.")
        if case_registry is None:
            raise ValueError("case_registry cannot be None.")

        self._approvals = approval_registry
        self._changes = change_registry
        self._cases = case_registry

    def record_decision(
        self,
        *,
        case_id: str,
        change_id: str,
        approval_id: str,
        reviewer: str,
        role: str,
        decision: ApprovalDecision,
        comment: str,
    ) -> PrivacyApprovalRecord:
        change = self._changes.get(change_id)
        case = self._cases.get(case_id)

        # ------------------------------------------------------------------
        # GOVERNANCE INTEGRITY CONTROL 1
        #
        # The change submitted for a decision MUST belong to the governance
        # case being decided.
        #
        # Without this check a caller could theoretically submit:
        #
        #   case_id   = CASE-A
        #   change_id = CHANGE-B
        #
        # and create approval evidence connecting unrelated governance
        # objects.
        # ------------------------------------------------------------------
        if case.change_id != change_id:
            raise ValueError(
                f"Change {change_id} does not belong to governance case "
                f"{case_id}."
            )

        # ------------------------------------------------------------------
        # GOVERNANCE INTEGRITY CONTROL 2
        #
        # APPROVED and BLOCKED are terminal governance states.
        #
        # Normal decision endpoints must not silently reopen or overwrite a
        # finalized governance case. A future reopen workflow, if required,
        # must be explicit and separately controlled.
        # ------------------------------------------------------------------
        if case.governance_status in {"APPROVED", "BLOCKED"}:
            raise ValueError(
                f"Governance case {case_id} already has a final decision."
            )

        record = PrivacyApprovalRecord(
            approval_id=approval_id,
            case_id=case_id,
            change_id=change_id,
            reviewer=reviewer,
            role=role.strip().upper(),
            decision=decision,
            comment=comment,
            decided_at=datetime.now(timezone.utc),
        )

        self._approvals.register(record)

        records = self._approvals.for_case(case_id)

        dpo_ok = any(
            r.role == "DPO"
            and r.decision == ApprovalDecision.APPROVED
            for r in records
        )

        grc_ok = any(
            r.role == "GRC"
            and r.decision == ApprovalDecision.APPROVED
            for r in records
        )

        rejected = any(
            r.decision == ApprovalDecision.REJECTED
            for r in records
        )

        changes_requested = any(
            r.decision == ApprovalDecision.REQUEST_CHANGES
            for r in records
        )

        if rejected or changes_requested:
            status = PrivacyChangeStatus.BLOCKED
            governance_status = "BLOCKED"

        elif (
            (not change.dpo_required or dpo_ok)
            and (not change.grc_required or grc_ok)
        ):
            status = PrivacyChangeStatus.APPROVED
            governance_status = "APPROVED"

        else:
            status = PrivacyChangeStatus.PENDING_DPO_GRC
            governance_status = "PENDING_DPO_GRC"

        self._changes.update(
            replace(
                change,
                status=status,
            )
        )

        self._cases.update(
            replace(
                case,
                governance_status=governance_status,
                final_decision=(
                    decision.value
                    if governance_status in {"APPROVED", "BLOCKED"}
                    else None
                ),
                final_decision_at=(
                    record.decided_at
                    if governance_status in {"APPROVED", "BLOCKED"}
                    else None
                ),
            )
        )

        return record