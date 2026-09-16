from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pytest

from app.application.privacy.privacy_approval_record import (
    ApprovalDecision,
    PrivacyApprovalRecord,
)
from app.application.privacy.privacy_approval_registry import (
    PrivacyApprovalRegistry,
)
from app.application.privacy.privacy_change import (
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)


@dataclass(frozen=True)
class FakeChange:
    change_id: str
    dpo_required: bool
    grc_required: bool
    status: PrivacyChangeStatus


@dataclass(frozen=True)
class FakeCase:
    case_id: str
    change_id: str
    governance_status: str
    final_decision: str | None = None
    final_decision_at: datetime | None = None


class FakeChangeRegistry:
    def __init__(self, changes: list[FakeChange]) -> None:
        self._changes = {
            change.change_id: change
            for change in changes
        }

    def get(self, change_id: str) -> FakeChange:
        return self._changes[change_id]

    def update(self, change: FakeChange) -> None:
        self._changes[change.change_id] = change


class FakeCaseRegistry:
    def __init__(self, cases: list[FakeCase]) -> None:
        self._cases = {
            case.case_id: case
            for case in cases
        }

    def get(self, case_id: str) -> FakeCase:
        return self._cases[case_id]

    def update(self, case: FakeCase) -> None:
        self._cases[case.case_id] = case


def _build_service(
    *,
    change_id: str = "CHANGE-A",
    case_id: str = "CASE-A",
    dpo_required: bool = True,
    grc_required: bool = True,
    governance_status: str = "PENDING_DPO_GRC",
) -> tuple[
    PrivacyGovernanceDecisionService,
    FakeChangeRegistry,
    FakeCaseRegistry,
    PrivacyApprovalRegistry,
]:
    change_registry = FakeChangeRegistry(
        [
            FakeChange(
                change_id=change_id,
                dpo_required=dpo_required,
                grc_required=grc_required,
                status=PrivacyChangeStatus.PENDING_DPO_GRC,
            )
        ]
    )

    case_registry = FakeCaseRegistry(
        [
            FakeCase(
                case_id=case_id,
                change_id=change_id,
                governance_status=governance_status,
            )
        ]
    )

    approval_registry = PrivacyApprovalRegistry()

    service = PrivacyGovernanceDecisionService(
        approval_registry=approval_registry,
        change_registry=change_registry,
        case_registry=case_registry,
    )

    return (
        service,
        change_registry,
        case_registry,
        approval_registry,
    )


def _approve(
    service: PrivacyGovernanceDecisionService,
    *,
    case_id: str,
    change_id: str,
    approval_id: str,
    reviewer: str,
    role: str,
) -> PrivacyApprovalRecord:
    return service.record_decision(
        case_id=case_id,
        change_id=change_id,
        approval_id=approval_id,
        reviewer=reviewer,
        role=role,
        decision=ApprovalDecision.APPROVED,
        comment=f"{role} approval",
    )


def test_dpo_and_grc_required_reach_approved_only_after_both_approvals() -> None:
    (
        service,
        change_registry,
        case_registry,
        approval_registry,
    ) = _build_service(
        dpo_required=True,
        grc_required=True,
    )

    dpo_record = _approve(
        service,
        case_id="CASE-A",
        change_id="CHANGE-A",
        approval_id="APR-DPO-001",
        reviewer="dpo@example.test",
        role="DPO",
    )

    assert dpo_record.decision == ApprovalDecision.APPROVED
    assert case_registry.get("CASE-A").governance_status == "PENDING_DPO_GRC"
    assert (
        change_registry.get("CHANGE-A").status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )
    assert len(approval_registry.for_case("CASE-A")) == 1

    grc_record = _approve(
        service,
        case_id="CASE-A",
        change_id="CHANGE-A",
        approval_id="APR-GRC-001",
        reviewer="grc@example.test",
        role="GRC",
    )

    assert grc_record.decision == ApprovalDecision.APPROVED

    case = case_registry.get("CASE-A")
    change = change_registry.get("CHANGE-A")

    assert case.governance_status == "APPROVED"
    assert case.final_decision == "APPROVED"
    assert case.final_decision_at is not None
    assert change.status == PrivacyChangeStatus.APPROVED
    assert len(approval_registry.for_case("CASE-A")) == 2


def test_rejection_blocks_governance_case() -> None:
    (
        service,
        change_registry,
        case_registry,
        approval_registry,
    ) = _build_service(
        dpo_required=True,
        grc_required=True,
    )

    record = service.record_decision(
        case_id="CASE-A",
        change_id="CHANGE-A",
        approval_id="APR-DPO-REJECT-001",
        reviewer="dpo@example.test",
        role="DPO",
        decision=ApprovalDecision.REJECTED,
        comment="Rejected during privacy review.",
    )

    assert record.decision == ApprovalDecision.REJECTED

    case = case_registry.get("CASE-A")
    change = change_registry.get("CHANGE-A")

    assert case.governance_status == "BLOCKED"
    assert case.final_decision == "REJECTED"
    assert case.final_decision_at is not None
    assert change.status == PrivacyChangeStatus.BLOCKED
    assert len(approval_registry.for_case("CASE-A")) == 1


def test_request_changes_blocks_governance_case() -> None:
    (
        service,
        change_registry,
        case_registry,
        approval_registry,
    ) = _build_service(
        dpo_required=True,
        grc_required=True,
    )

    record = service.record_decision(
        case_id="CASE-A",
        change_id="CHANGE-A",
        approval_id="APR-DPO-CHANGES-001",
        reviewer="dpo@example.test",
        role="DPO",
        decision=ApprovalDecision.REQUEST_CHANGES,
        comment="Additional safeguards are required.",
    )

    assert record.decision == ApprovalDecision.REQUEST_CHANGES

    case = case_registry.get("CASE-A")
    change = change_registry.get("CHANGE-A")

    assert case.governance_status == "BLOCKED"
    assert case.final_decision == "REQUEST_CHANGES"
    assert case.final_decision_at is not None
    assert change.status == PrivacyChangeStatus.BLOCKED
    assert len(approval_registry.for_case("CASE-A")) == 1


def test_case_and_change_mismatch_is_rejected() -> None:
    (
        service,
        change_registry,
        case_registry,
        approval_registry,
    ) = _build_service(
        case_id="CASE-A",
        change_id="CHANGE-A",
    )

    # Add a different change that does NOT belong to CASE-A.
    change_registry.update(
        FakeChange(
            change_id="CHANGE-B",
            dpo_required=True,
            grc_required=True,
            status=PrivacyChangeStatus.PENDING_DPO_GRC,
        )
    )

    with pytest.raises(
        ValueError,
        match="does not belong to governance case CASE-A",
    ):
        service.record_decision(
            case_id="CASE-A",
            change_id="CHANGE-B",
            approval_id="APR-MISMATCH-001",
            reviewer="dpo@example.test",
            role="DPO",
            decision=ApprovalDecision.APPROVED,
            comment="Should never be recorded.",
        )

    assert approval_registry.all() == ()

    assert (
        case_registry.get("CASE-A").governance_status
        == "PENDING_DPO_GRC"
    )

    assert (
        change_registry.get("CHANGE-B").status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )


def test_finalized_approved_case_cannot_receive_another_decision() -> None:
    (
        service,
        change_registry,
        case_registry,
        approval_registry,
    ) = _build_service(
        dpo_required=False,
        grc_required=False,
    )

    first = _approve(
        service,
        case_id="CASE-A",
        change_id="CHANGE-A",
        approval_id="APR-APPROVED-001",
        reviewer="dpo@example.test",
        role="DPO",
    )

    assert first.decision == ApprovalDecision.APPROVED
    assert case_registry.get("CASE-A").governance_status == "APPROVED"

    with pytest.raises(
        ValueError,
        match="already has a final decision",
    ):
        service.record_decision(
            case_id="CASE-A",
            change_id="CHANGE-A",
            approval_id="APR-LATE-REJECT-001",
            reviewer="grc@example.test",
            role="GRC",
            decision=ApprovalDecision.REJECTED,
            comment="This must not overwrite the final decision.",
        )

    assert len(approval_registry.for_case("CASE-A")) == 1
    assert (
        approval_registry.for_case("CASE-A")[0].approval_id
        == "APR-APPROVED-001"
    )

    assert (
        case_registry.get("CASE-A").governance_status
        == "APPROVED"
    )

    assert (
        change_registry.get("CHANGE-A").status
        == PrivacyChangeStatus.APPROVED
    )


def test_finalized_blocked_case_cannot_receive_another_decision() -> None:
    (
        service,
        change_registry,
        case_registry,
        approval_registry,
    ) = _build_service(
        dpo_required=True,
        grc_required=True,
    )

    first = service.record_decision(
        case_id="CASE-A",
        change_id="CHANGE-A",
        approval_id="APR-BLOCKED-001",
        reviewer="dpo@example.test",
        role="DPO",
        decision=ApprovalDecision.REJECTED,
        comment="Privacy rejection.",
    )

    assert first.decision == ApprovalDecision.REJECTED
    assert case_registry.get("CASE-A").governance_status == "BLOCKED"

    with pytest.raises(
        ValueError,
        match="already has a final decision",
    ):
        service.record_decision(
            case_id="CASE-A",
            change_id="CHANGE-A",
            approval_id="APR-LATE-APPROVAL-001",
            reviewer="grc@example.test",
            role="GRC",
            decision=ApprovalDecision.APPROVED,
            comment="This must not reopen the case.",
        )

    assert len(approval_registry.for_case("CASE-A")) == 1
    assert (
        case_registry.get("CASE-A").governance_status
        == "BLOCKED"
    )
    assert (
        change_registry.get("CHANGE-A").status
        == PrivacyChangeStatus.BLOCKED
    )
