from __future__ import annotations

from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_governance_composition import (
    create_privacy_governance_composition,
)


def make_change(change_id: str) -> PrivacyChange:
    return PrivacyChange(
        change_id=change_id,
        title="6G lifecycle test",
        description="Human decision lifecycle test.",
        risk=PrivacyChangeRisk.MEDIUM,
        dpo_required=True,
        grc_required=True,
    )


def test_dpo_then_grc_reaches_approved_with_two_records() -> None:
    composition = create_privacy_governance_composition()

    result = composition.flow_service.process_new_processing(
        make_change("PCR-6G-LIFE-001"),
        automated_validation_passed=True,
        case_id="CASE-6G-LIFE-001",
        trigger_source="Processing Registry",
    )

    assert result.case.governance_status == "PENDING_DPO_GRC"

    composition.case_service.approve(
        case_id="CASE-6G-LIFE-001",
        change_id="PCR-6G-LIFE-001",
        approval_id="APR-DPO-6G-LIFE-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO approved.",
    )

    assert (
        composition.case_registry.get(
            "CASE-6G-LIFE-001"
        ).governance_status
        == "PENDING_DPO_GRC"
    )

    composition.case_service.approve(
        case_id="CASE-6G-LIFE-001",
        change_id="PCR-6G-LIFE-001",
        approval_id="APR-GRC-6G-LIFE-001",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="GRC approved.",
    )

    case = composition.case_registry.get("CASE-6G-LIFE-001")
    change = composition.change_registry.get("PCR-6G-LIFE-001")

    assert case.governance_status == "APPROVED"
    assert case.final_decision == "APPROVED"
    assert change.status == PrivacyChangeStatus.APPROVED
    assert len(
        composition.approval_registry.for_case(
            "CASE-6G-LIFE-001"
        )
    ) == 2


def test_rejection_reaches_blocked() -> None:
    composition = create_privacy_governance_composition()

    composition.flow_service.process_new_processing(
        make_change("PCR-6G-LIFE-002"),
        automated_validation_passed=True,
        case_id="CASE-6G-LIFE-002",
        trigger_source="Processing Registry",
    )

    record = composition.case_service.reject(
        case_id="CASE-6G-LIFE-002",
        change_id="PCR-6G-LIFE-002",
        approval_id="APR-DPO-6G-LIFE-002",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="Privacy evidence is insufficient.",
    )

    case = composition.case_registry.get("CASE-6G-LIFE-002")
    change = composition.change_registry.get("PCR-6G-LIFE-002")

    assert record.decision.value == "REJECTED"
    assert case.governance_status == "BLOCKED"
    assert case.final_decision == "REJECTED"
    assert change.status == PrivacyChangeStatus.BLOCKED


def test_request_changes_reaches_blocked() -> None:
    composition = create_privacy_governance_composition()

    composition.flow_service.process_new_processing(
        make_change("PCR-6G-LIFE-003"),
        automated_validation_passed=True,
        case_id="CASE-6G-LIFE-003",
        trigger_source="Processing Registry",
    )

    record = composition.case_service.request_changes(
        case_id="CASE-6G-LIFE-003",
        change_id="PCR-6G-LIFE-003",
        approval_id="APR-GRC-6G-LIFE-003",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="Additional controls required.",
    )

    case = composition.case_registry.get("CASE-6G-LIFE-003")

    assert record.decision.value == "REQUEST_CHANGES"
    assert case.governance_status == "BLOCKED"
    assert case.final_decision == "REQUEST_CHANGES"

