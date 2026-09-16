from datetime import datetime, timezone

from app.application.privacy.privacy_approval_record import (
    ApprovalDecision,
)
from app.application.privacy.privacy_approval_registry import (
    PrivacyApprovalRegistry,
)
from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from app.application.privacy.privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)


def make_change() -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-001",
        title="New processing",
        description="Controlled governance test.",
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )


def make_case() -> PrivacyGovernanceCase:
    return PrivacyGovernanceCase(
        case_id="CASE-001",
        title="New processing",
        summary="Controlled governance test.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        # Governance integrity link:
        # this case explicitly owns PCR-001.
        change_id="PCR-001",
    )


def make_change_registry() -> PrivacyChangeRegistry:
    """Build the existing application registry using its real contract."""

    registry = PrivacyChangeRegistry()
    registry.register(make_change())

    return registry


def make_service() -> tuple[
    PrivacyGovernanceDecisionService,
    PrivacyGovernanceCaseRegistry,
    PrivacyChangeRegistry,
]:
    """Build the governance decision service with linked test fixtures."""

    changes = make_change_registry()

    cases = PrivacyGovernanceCaseRegistry(
        [make_case()]
    )

    approvals = PrivacyApprovalRegistry()

    service = PrivacyGovernanceDecisionService(
        approval_registry=approvals,
        change_registry=changes,
        case_registry=cases,
    )

    return service, cases, changes


def test_two_explicit_approvals_move_case_to_approved() -> None:
    service, cases, changes = make_service()

    # ---------------------------------------------------------
    # DPO approval
    # ---------------------------------------------------------

    service.record_decision(
        case_id="CASE-001",
        change_id="PCR-001",
        approval_id="APR-DPO-001",
        reviewer="DPO",
        role="DPO",
        decision=ApprovalDecision.APPROVED,
        comment="Reviewed.",
    )

    # One required approval is not sufficient.
    assert (
        cases.get(
            "CASE-001"
        ).governance_status
        == "PENDING_DPO_GRC"
    )

    assert (
        changes.get(
            "PCR-001"
        ).status
        == PrivacyChangeStatus.PENDING_DPO_GRC
    )

    # ---------------------------------------------------------
    # GRC approval
    # ---------------------------------------------------------

    service.record_decision(
        case_id="CASE-001",
        change_id="PCR-001",
        approval_id="APR-GRC-001",
        reviewer="GRC",
        role="GRC",
        decision=ApprovalDecision.APPROVED,
        comment="Reviewed.",
    )

    # Both required human approvals are now recorded.
    assert (
        cases.get(
            "CASE-001"
        ).governance_status
        == "APPROVED"
    )

    assert (
        cases.get(
            "CASE-001"
        ).final_decision
        == "APPROVED"
    )

    assert (
        cases.get(
            "CASE-001"
        ).final_decision_at
        is not None
    )

    assert (
        changes.get(
            "PCR-001"
        ).status
        == PrivacyChangeStatus.APPROVED
    )


def test_rejection_blocks_case() -> None:
    service, cases, changes = make_service()

    service.record_decision(
        case_id="CASE-001",
        change_id="PCR-001",
        approval_id="APR-DPO-001",
        reviewer="DPO",
        role="DPO",
        decision=ApprovalDecision.REJECTED,
        comment="Rejected pending remediation.",
    )

    assert (
        cases.get(
            "CASE-001"
        ).governance_status
        == "BLOCKED"
    )

    assert (
        cases.get(
            "CASE-001"
        ).final_decision
        == "REJECTED"
    )

    assert (
        cases.get(
            "CASE-001"
        ).final_decision_at
        is not None
    )

    assert (
        changes.get(
            "PCR-001"
        ).status
        == PrivacyChangeStatus.BLOCKED
    )
