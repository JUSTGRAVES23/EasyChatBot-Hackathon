from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.privacy_governance import router as privacy_governance_router
from app.application.privacy.privacy_approval_record import (
    ApprovalDecision,
)
from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
    reset_privacy_governance_composition_for_tests,
)


def make_app() -> FastAPI:
    """Create a minimal API application using the real governance router."""

    app = FastAPI()

    app.include_router(
        privacy_governance_router,
    )

    return app


def make_change(
    change_id: str = "PCR-E2E-001",
) -> PrivacyChange:
    return PrivacyChange(
        change_id=change_id,
        title="E2E learner processing",
        description="End-to-end privacy governance runtime test.",
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )


def setup_function() -> None:
    """Ensure every E2E test starts with a clean runtime composition."""

    reset_privacy_governance_composition_for_tests()


def teardown_function() -> None:
    """Prevent runtime governance state leaking between tests."""

    reset_privacy_governance_composition_for_tests()


def test_runtime_pass_flow_is_visible_through_api_and_reaches_approved():
    composition = get_privacy_governance_composition()

    # ---------------------------------------------------------
    # 1. Submit a real NEW_PROCESSING through the runtime flow.
    # ---------------------------------------------------------

    result = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
        case_id="CASE-E2E-001",
        trigger_source="Processing Registry",
    )

    # ---------------------------------------------------------
    # 2. Validation PASS.
    # ---------------------------------------------------------

    assert result.case.validation_status == "PASS"

    # ---------------------------------------------------------
    # 3. Governance case starts PENDING_DPO_GRC.
    # ---------------------------------------------------------

    assert result.case.governance_status == "PENDING_DPO_GRC"

    # ---------------------------------------------------------
    # 4. The same case is visible through the dashboard service.
    # ---------------------------------------------------------

    dashboard_cases = composition.dashboard_service.case_list()

    assert len(dashboard_cases) == 1
    assert dashboard_cases[0]["case_id"] == "CASE-E2E-001"
    assert dashboard_cases[0]["governance_status"] == "PENDING_DPO_GRC"

    # ---------------------------------------------------------
    # 5. The API reads the SAME runtime composition.
    # ---------------------------------------------------------

    app = make_app()
    client = TestClient(app)

    summary_response = client.get(
        "/api/privacy/governance/summary",
    )

    assert summary_response.status_code == 200
    assert summary_response.json() == {
        "total_cases": 1,
        "pending": 1,
        "approved": 0,
        "blocked": 0,
        "approval_records": 0,
    }

    cases_response = client.get(
        "/api/privacy/governance/cases",
    )

    assert cases_response.status_code == 200

    cases = cases_response.json()

    assert len(cases) == 1
    assert cases[0]["case_id"] == "CASE-E2E-001"
    assert cases[0]["trigger_type"] == "NEW_PROCESSING"
    assert cases[0]["governance_status"] == "PENDING_DPO_GRC"

    # ---------------------------------------------------------
    # 6. Verify case detail is exposed by the API.
    # ---------------------------------------------------------

    detail_response = client.get(
        "/api/privacy/governance/cases/CASE-E2E-001",
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["case_id"] == "CASE-E2E-001"
    assert detail["trigger"]["type"] == "NEW_PROCESSING"
    assert detail["governance_status"] == "PENDING_DPO_GRC"
    assert detail["approval_history"] == []

    # ---------------------------------------------------------
    # 7. DPO approval.
    # ---------------------------------------------------------

    dpo_record = composition.case_service.approve(
        case_id="CASE-E2E-001",
        change_id="PCR-E2E-001",
        approval_id="APR-E2E-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO approval completed.",
    )

    assert dpo_record.decision == ApprovalDecision.APPROVED

    # One of two required approvals is not enough.
    assert (
        composition.case_registry.get(
            "CASE-E2E-001",
        ).governance_status
        == "PENDING_DPO_GRC"
    )

    # ---------------------------------------------------------
    # 8. GRC approval.
    # ---------------------------------------------------------

    grc_record = composition.case_service.approve(
        case_id="CASE-E2E-001",
        change_id="PCR-E2E-001",
        approval_id="APR-E2E-GRC-001",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="GRC approval completed.",
    )

    assert grc_record.decision == ApprovalDecision.APPROVED

    # ---------------------------------------------------------
    # 9. Case becomes APPROVED.
    # ---------------------------------------------------------

    case = composition.case_registry.get(
        "CASE-E2E-001",
    )

    change = composition.change_registry.get(
        "PCR-E2E-001",
    )

    assert case.governance_status == "APPROVED"
    assert case.final_decision == "APPROVED"
    assert case.final_decision_at is not None
    assert change.status == PrivacyChangeStatus.APPROVED

    # ---------------------------------------------------------
    # 10. Dashboard reaches expected final state.
    # ---------------------------------------------------------

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 1,
        "blocked": 0,
        "approval_records": 2,
    }

    # ---------------------------------------------------------
    # Final API verification.
    # ---------------------------------------------------------

    final_summary_response = client.get(
        "/api/privacy/governance/summary",
    )

    assert final_summary_response.status_code == 200

    assert final_summary_response.json() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 1,
        "blocked": 0,
        "approval_records": 2,
    }

    final_detail_response = client.get(
        "/api/privacy/governance/cases/CASE-E2E-001",
    )

    assert final_detail_response.status_code == 200

    final_detail = final_detail_response.json()

    assert final_detail["governance_status"] == "APPROVED"
    assert final_detail["final_decision"] == "APPROVED"
    assert len(final_detail["approval_history"]) == 2


def test_runtime_failed_validation_creates_blocked_case_visible_in_dashboard():
    composition = get_privacy_governance_composition()

    # ---------------------------------------------------------
    # Validation FAIL.
    # ---------------------------------------------------------

    result = composition.flow_service.process_new_processing(
        make_change(
            change_id="PCR-E2E-BLOCKED-001",
        ),
        automated_validation_passed=False,
        case_id="CASE-E2E-BLOCKED-001",
        trigger_source="Processing Registry",
    )

    # ---------------------------------------------------------
    # Change and case must both be BLOCKED.
    # ---------------------------------------------------------

    assert result.change.status == PrivacyChangeStatus.BLOCKED
    assert result.case.validation_status == "FAIL"
    assert result.case.governance_status == "BLOCKED"

    assert (
        composition.change_registry.get(
            "PCR-E2E-BLOCKED-001",
        ).status
        == PrivacyChangeStatus.BLOCKED
    )

    assert (
        composition.case_registry.get(
            "CASE-E2E-BLOCKED-001",
        ).governance_status
        == "BLOCKED"
    )

    # ---------------------------------------------------------
    # Dashboard must expose the blocked case.
    # ---------------------------------------------------------

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 0,
        "blocked": 1,
        "approval_records": 0,
    }

    cases = composition.dashboard_service.case_list()

    assert len(cases) == 1
    assert cases[0]["case_id"] == "CASE-E2E-BLOCKED-001"
    assert cases[0]["validation_status"] == "FAIL"
    assert cases[0]["governance_status"] == "BLOCKED"

    # ---------------------------------------------------------
    # API must expose the same blocked state.
    # ---------------------------------------------------------

    app = make_app()
    client = TestClient(app)

    response = client.get(
        "/api/privacy/governance/summary",
    )

    assert response.status_code == 200

    assert response.json() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 0,
        "blocked": 1,
        "approval_records": 0,
    }

    cases_response = client.get(
        "/api/privacy/governance/cases",
    )

    assert cases_response.status_code == 200

    cases = cases_response.json()

    assert len(cases) == 1
    assert cases[0]["case_id"] == "CASE-E2E-BLOCKED-001"
    assert cases[0]["governance_status"] == "BLOCKED"
    assert cases[0]["validation_status"] == "FAIL"
