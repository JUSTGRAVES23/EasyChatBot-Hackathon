from __future__ import annotations

from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_governance_composition import (
    create_privacy_governance_composition,
)


def make_change() -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-FLOW-001",
        title="New learner processing",
        description="A new learner processing activity requires governance.",
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )


def test_new_processing_pass_creates_pending_governance_case_in_shared_registry():
    composition = create_privacy_governance_composition()

    result = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
    )

    assert result.change.status == PrivacyChangeStatus.PENDING_DPO_GRC
    assert result.case.case_id == "CASE-PCR-FLOW-001"
    assert result.case.trigger_type.value == "NEW_PROCESSING"
    assert result.case.validation_status == "PASS"
    assert result.case.governance_status == "PENDING_DPO_GRC"

    assert composition.case_registry.get(
        "CASE-PCR-FLOW-001"
    ) is result.case

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 1,
        "approved": 0,
        "blocked": 0,
        "approval_records": 0,
    }


def test_dpo_and_grc_approvals_update_the_same_case_seen_by_dashboard():
    composition = create_privacy_governance_composition()

    result = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
    )

    composition.case_service.approve(
        case_id=result.case.case_id,
        change_id="PCR-FLOW-001",
        approval_id="APR-FLOW-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO approved.",
    )

    assert composition.dashboard_service.summary()["pending"] == 1
    assert composition.dashboard_service.summary()["approved"] == 0

    composition.case_service.approve(
        case_id=result.case.case_id,
        change_id="PCR-FLOW-001",
        approval_id="APR-FLOW-GRC-001",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="GRC approved.",
    )

    assert composition.case_registry.get(
        result.case.case_id
    ).governance_status == "APPROVED"

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 1,
        "blocked": 0,
        "approval_records": 2,
    }


def test_rejected_case_is_blocked_and_visible_to_dashboard():
    composition = create_privacy_governance_composition()

    result = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
    )

    composition.case_service.reject(
        case_id=result.case.case_id,
        change_id="PCR-FLOW-001",
        approval_id="APR-FLOW-DPO-REJECT",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="Additional remediation required.",
    )

    assert composition.case_registry.get(
        result.case.case_id
    ).governance_status == "BLOCKED"

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 0,
        "blocked": 1,
        "approval_records": 1,
    }


def test_failed_validation_blocks_change_and_creates_blocked_case():
    composition = create_privacy_governance_composition()

    result = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=False,
    )

    assert result.change.status == PrivacyChangeStatus.BLOCKED
    assert result.case.validation_status == "FAIL"
    assert result.case.governance_status == "BLOCKED"

    assert composition.dashboard_service.summary()["blocked"] == 1


def test_flow_is_idempotent_for_same_case_identifier():
    composition = create_privacy_governance_composition()

    first = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
    )

    second = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
    )

    assert second.case is first.case
    assert len(composition.case_registry.all()) == 1

