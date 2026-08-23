from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.application.privacy.privacy_approval_record import (
    ApprovalDecision,
)
from backend.app.application.privacy.privacy_approval_registry import (
    PrivacyApprovalRegistry,
)
from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from backend.app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from backend.app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from backend.app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from backend.app.application.privacy.privacy_governance_case_service import (
    PrivacyGovernanceCaseService,
)
from backend.app.application.privacy.privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)


def make_change() -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-CASE-001",
        title="Controlled privacy change",
        description="Case service integration test.",
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )


def make_case() -> PrivacyGovernanceCase:
    return PrivacyGovernanceCase(
        case_id="CASE-001",
        title="Controlled privacy case",
        summary="Case service integration test.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        risk="MEDIUM",
        validation_status="PASS",
        email_status="SENT",
        governance_status="PENDING_DPO_GRC",
    )


def make_service():
    changes = PrivacyChangeRegistry()
    changes.register(make_change())

    cases = PrivacyGovernanceCaseRegistry(
        [make_case()]
    )

    approvals = PrivacyApprovalRegistry()

    decision_service = PrivacyGovernanceDecisionService(
        approval_registry=approvals,
        change_registry=changes,
        case_registry=cases,
    )

    service = PrivacyGovernanceCaseService(
        case_registry=cases,
        change_registry=changes,
        approval_registry=approvals,
        decision_service=decision_service,
    )

    return (
        service,
        changes,
        cases,
        approvals,
    )


def test_get_case_returns_case_by_identifier():
    service, _, _, _ = make_service()

    case = service.get_case("CASE-001")

    assert case.case_id == "CASE-001"
    assert case.title == "Controlled privacy case"


def test_list_cases_returns_registered_cases():
    service, _, _, _ = make_service()

    cases = service.list_cases()

    assert len(cases) == 1
    assert cases[0].case_id == "CASE-001"


def test_list_pending_cases_returns_pending_cases():
    service, _, _, _ = make_service()

    pending = service.list_pending_cases()

    assert len(pending) == 1
    assert pending[0].case_id == "CASE-001"


def test_get_approval_history_is_empty_before_decisions():
    service, _, _, _ = make_service()

    history = service.get_approval_history(
        "CASE-001"
    )

    assert history == ()


def test_approve_delegates_to_decision_service():
    service, changes, cases, approvals = make_service()

    record = service.approve(
        case_id="CASE-001",
        change_id="PCR-CASE-001",
        approval_id="APR-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO review completed.",
    )

    assert record.decision == ApprovalDecision.APPROVED
    assert record.case_id == "CASE-001"
    assert record.change_id == "PCR-CASE-001"

    assert len(
        approvals.for_case("CASE-001")
    ) == 1

    # One approval is not sufficient because GRC is also required.
    assert (
        cases.get("CASE-001").governance_status
        == "PENDING_DPO_GRC"
    )

    assert (
        changes.get("PCR-CASE-001").status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )


def test_two_required_approvals_move_case_to_approved():
    service, changes, cases, approvals = make_service()

    service.approve(
        case_id="CASE-001",
        change_id="PCR-CASE-001",
        approval_id="APR-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO approved.",
    )

    service.approve(
        case_id="CASE-001",
        change_id="PCR-CASE-001",
        approval_id="APR-GRC-001",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="GRC approved.",
    )

    case = cases.get("CASE-001")
    change = changes.get("PCR-CASE-001")

    assert case.governance_status == "APPROVED"
    assert case.final_decision == "APPROVED"
    assert case.final_decision_at is not None

    assert change.status == PrivacyChangeStatus.APPROVED

    assert len(
        approvals.for_case("CASE-001")
    ) == 2


def test_reject_blocks_case():
    service, changes, cases, approvals = make_service()

    record = service.reject(
        case_id="CASE-001",
        change_id="PCR-CASE-001",
        approval_id="APR-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="Rejected pending remediation.",
    )

    assert record.decision == ApprovalDecision.REJECTED

    case = cases.get("CASE-001")
    change = changes.get("PCR-CASE-001")

    assert case.governance_status == "BLOCKED"
    assert case.final_decision == "REJECTED"
    assert case.final_decision_at is not None

    assert change.status == PrivacyChangeStatus.BLOCKED

    assert len(
        approvals.for_case("CASE-001")
    ) == 1


def test_request_changes_blocks_case():
    service, changes, cases, approvals = make_service()

    record = service.request_changes(
        case_id="CASE-001",
        change_id="PCR-CASE-001",
        approval_id="APR-GRC-001",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="Additional privacy evidence required.",
    )

    assert (
        record.decision
        == ApprovalDecision.REQUEST_CHANGES
    )

    assert (
        cases.get("CASE-001").governance_status
        == "BLOCKED"
    )

    assert (
        cases.get("CASE-001").final_decision
        == "REQUEST_CHANGES"
    )

    assert (
        changes.get("PCR-CASE-001").status
        == PrivacyChangeStatus.BLOCKED
    )

    assert len(
        approvals.for_case("CASE-001")
    ) == 1


def test_get_unknown_case_raises_key_error():
    service, _, _, _ = make_service()

    with pytest.raises(
        KeyError,
        match="Governance case not found",
    ):
        service.get_case(
            "DOES-NOT-EXIST"
        )


def test_approval_history_requires_existing_case():
    service, _, _, _ = make_service()

    with pytest.raises(
        KeyError,
        match="Governance case not found",
    ):
        service.get_approval_history(
            "DOES-NOT-EXIST"
        )


def test_empty_case_id_is_rejected():
    service, _, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="case_id is required",
    ):
        service.get_case("")


def test_missing_reviewer_is_rejected():
    service, _, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="reviewer is required",
    ):
        service.approve(
            case_id="CASE-001",
            change_id="PCR-CASE-001",
            approval_id="APR-001",
            reviewer="",
            role="DPO",
            comment="Review.",
        )


def test_unknown_change_is_rejected_before_decision():
    service, _, _, _ = make_service()

    with pytest.raises(
        KeyError,
        match="Privacy change not found",
    ):
        service.approve(
            case_id="CASE-001",
            change_id="DOES-NOT-EXIST",
            approval_id="APR-001",
            reviewer="DPO Reviewer",
            role="DPO",
            comment="Review.",
        )


def test_approval_history_contains_record_after_decision():
    service, _, _, _ = make_service()

    service.approve(
        case_id="CASE-001",
        change_id="PCR-CASE-001",
        approval_id="APR-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="Reviewed.",
    )

    history = service.get_approval_history(
        "CASE-001"
    )

    assert len(history) == 1
    assert history[0].approval_id == "APR-DPO-001"
    assert history[0].reviewer == "DPO Reviewer"
    assert history[0].role == "DPO"
    assert (
        history[0].decision
        == ApprovalDecision.APPROVED
    )