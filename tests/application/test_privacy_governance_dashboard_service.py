from datetime import datetime, timezone

from backend.app.application.privacy.privacy_approval_registry import (
    PrivacyApprovalRegistry,
)
from backend.app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from backend.app.application.privacy.privacy_governance_case_registry import (
    PrivacyGovernanceCaseRegistry,
)
from backend.app.application.privacy.privacy_governance_dashboard_service import (
    PrivacyGovernanceDashboardService,
)


def test_dashboard_exposes_clickable_case_identifier_and_trigger():
    case = PrivacyGovernanceCase(
        case_id="PCR-001",
        title="New data mapping",
        summary="A new learner data mapping was registered.",
        trigger_type=PrivacyTriggerType.DATA_MAPPING_CHANGE,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Data Processing Map",
        risk="HIGH",
        validation_status="PASS",
        email_status="SENT",
    )

    service = PrivacyGovernanceDashboardService(
        case_registry=PrivacyGovernanceCaseRegistry([case]),
        approval_registry=PrivacyApprovalRegistry(),
    )

    row = service.case_list()[0]
    detail = service.case_detail("PCR-001")

    assert row["case_id"] == "PCR-001"
    assert row["summary"] == "A new learner data mapping was registered."
    assert row["trigger_type"] == "DATA_MAPPING_CHANGE"
    assert row["validation_status"] == "PASS"
    assert detail["trigger"]["source"] == "Data Processing Map"


def test_dashboard_status_chart_contains_governance_status_counts():
    pending = PrivacyGovernanceCase(
        case_id="PCR-PENDING",
        title="Pending case",
        summary="Pending review.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        governance_status="PENDING_DPO_GRC",
    )
    approved = PrivacyGovernanceCase(
        case_id="PCR-APPROVED",
        title="Approved case",
        summary="Approved.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        governance_status="APPROVED",
    )
    blocked = PrivacyGovernanceCase(
        case_id="PCR-BLOCKED",
        title="Blocked case",
        summary="Rejected.",
        trigger_type=PrivacyTriggerType.NEW_PROCESSING,
        triggered_at=datetime.now(timezone.utc),
        trigger_source="Processing Registry",
        governance_status="BLOCKED",
    )

    service = PrivacyGovernanceDashboardService(
        case_registry=PrivacyGovernanceCaseRegistry(
            [pending, approved, blocked]
        ),
        approval_registry=PrivacyApprovalRegistry(),
    )

    assert service.status_chart() == (
        {"status": "Pending DPO/GRC", "count": 1},
        {"status": "Approved", "count": 1},
        {"status": "Rejected / Blocked", "count": 1},
    )
