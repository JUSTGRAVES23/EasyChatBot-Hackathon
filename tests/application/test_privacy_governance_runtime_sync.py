from __future__ import annotations

from datetime import datetime, timezone

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
from app.application.privacy.privacy_governance_case_service import (
    PrivacyGovernanceCaseService,
)
from app.application.privacy.privacy_governance_decision_service import (
    PrivacyGovernanceDecisionService,
)
from app.application.privacy.privacy_governance_runtime_sync import (
    PrivacyGovernanceRuntimeSync,
)


class FakeExcelSync:
    """Deterministic Excel synchronization test double."""

    def __init__(self) -> None:
        self.case_rows: list[PrivacyGovernanceCase] = []
        self.approval_case_ids: list[str] = []

    def sync_case(
        self,
        case: PrivacyGovernanceCase,
    ) -> None:
        self.case_rows.append(case)

    def sync_approval(
        self,
        case_id: str,
    ) -> None:
        self.approval_case_ids.append(case_id)


def make_change() -> PrivacyChange:
    return PrivacyChange(
        change_id="PCR-SYNC-001",
        title="Runtime sync test",
        description="Runtime Excel synchronization test.",
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )


def make_case() -> PrivacyGovernanceCase:
    return PrivacyGovernanceCase(
        case_id="CASE-SYNC-001",
        title="Runtime sync test",
        summary="Runtime Excel synchronization test.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        change_id="PCR-SYNC-001",
        risk="MEDIUM",
        validation_status="PASS",
        email_status="SENT",
        governance_status="PENDING_DPO_GRC",
    )


def make_service() -> PrivacyGovernanceCaseService:
    changes = PrivacyChangeRegistry()

    changes.register(
        make_change()
    )

    cases = PrivacyGovernanceCaseRegistry()

    cases.register(
        make_case()
    )

    approvals = PrivacyApprovalRegistry()

    decision_service = PrivacyGovernanceDecisionService(
        approval_registry=approvals,
        change_registry=changes,
        case_registry=cases,
    )

    return PrivacyGovernanceCaseService(
        case_registry=cases,
        change_registry=changes,
        approval_registry=approvals,
        decision_service=decision_service,
    )


def test_sync_case_projects_authoritative_case():
    excel = FakeExcelSync()
    service = make_service()

    runtime_sync = PrivacyGovernanceRuntimeSync(
        case_service=service,
        excel_sync=excel,
    )

    result = runtime_sync.sync_case(
        "CASE-SYNC-001"
    )

    assert result.case_id == "CASE-SYNC-001"
    assert result.change_id == "PCR-SYNC-001"
    assert result.title == "Runtime sync test"
    assert result.risk == "MEDIUM"
    assert result.validation_status == "PASS"
    assert result.governance_status == "PENDING_DPO_GRC"

    assert len(
        excel.case_rows
    ) == 1

    projected_case = excel.case_rows[0]

    assert (
        projected_case.case_id
        == "CASE-SYNC-001"
    )

    assert (
        projected_case.change_id
        == "PCR-SYNC-001"
    )

    assert (
        projected_case.governance_status
        == "PENDING_DPO_GRC"
    )


def test_sync_decision_projects_case_and_approval_evidence():
    excel = FakeExcelSync()
    service = make_service()

    runtime_sync = PrivacyGovernanceRuntimeSync(
        case_service=service,
        excel_sync=excel,
    )

    approval = service.approve(
        case_id="CASE-SYNC-001",
        change_id="PCR-SYNC-001",
        approval_id="APR-SYNC-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO approval recorded.",
    )

    assert approval.case_id == "CASE-SYNC-001"
    assert approval.change_id == "PCR-SYNC-001"

    result = runtime_sync.sync_decision(
        "CASE-SYNC-001"
    )

    assert result.case_id == "CASE-SYNC-001"
    assert result.change_id == "PCR-SYNC-001"

    assert len(
        excel.case_rows
    ) == 1

    projected_case = excel.case_rows[0]

    assert (
        projected_case.case_id
        == "CASE-SYNC-001"
    )

    assert (
        projected_case.change_id
        == "PCR-SYNC-001"
    )

    assert (
        projected_case.governance_status
        == "PENDING_DPO_GRC"
    )

    assert excel.approval_case_ids == [
        "CASE-SYNC-001"
    ]
