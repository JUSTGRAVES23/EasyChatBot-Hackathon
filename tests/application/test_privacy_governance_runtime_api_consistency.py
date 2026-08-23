from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.privacy_governance import router
from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from backend.app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
    reset_privacy_governance_composition_for_tests,
)


@pytest.fixture(autouse=True)
def reset_runtime_composition():
    """
    Keep each test isolated while preserving the production singleton model.

    Production code uses the process-wide composition.
    Tests reset that composition between scenarios.
    """

    reset_privacy_governance_composition_for_tests()

    yield

    reset_privacy_governance_composition_for_tests()


def make_app() -> FastAPI:
    """Create a minimal FastAPI application using the real governance router."""

    application = FastAPI()

    application.include_router(
        router,
    )

    return application


def make_change(
    *,
    change_id: str = "PCR-CONSISTENCY-001",
) -> PrivacyChange:
    """Create a deterministic privacy-impacting change for the test."""

    return PrivacyChange(
        change_id=change_id,
        title="New learner processing",
        description=(
            "A new learner processing activity requiring "
            "privacy governance review."
        ),
        risk=PrivacyChangeRisk.MEDIUM,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
        created_at=datetime.now(timezone.utc),
    )


def test_runtime_and_api_share_the_same_governance_state():
    """
    Prove that the real runtime flow and the FastAPI API observe
    the same process-wide governance composition.

    Flow:

        NEW_PROCESSING
              ↓
        Validation PASS
              ↓
        PENDING_DPO_GRC
              ↓
        Dashboard
              ↓
        FastAPI API
              ↓
        DPO approval
              ↓
        GRC approval
              ↓
        APPROVED
    """

    composition = get_privacy_governance_composition()

    # ---------------------------------------------------------
    # 1. Submit a real NEW_PROCESSING through the runtime flow.
    # ---------------------------------------------------------

    result = composition.flow_service.process_new_processing(
        make_change(),
        automated_validation_passed=True,
        case_id="CASE-CONSISTENCY-001",
        trigger_source="Processing Registry",
    )

    # ---------------------------------------------------------
    # 2. Runtime state.
    # ---------------------------------------------------------

    assert result.change.status == PrivacyChangeStatus.PENDING_DPO_GRC

    assert result.case.case_id == "CASE-CONSISTENCY-001"
    assert result.case.validation_status == "PASS"
    assert result.case.governance_status == "PENDING_DPO_GRC"

    # ---------------------------------------------------------
    # 3. Dashboard service must see the same case.
    # ---------------------------------------------------------

    dashboard_cases = composition.dashboard_service.case_list()

    assert len(dashboard_cases) == 1

    assert dashboard_cases[0]["case_id"] == "CASE-CONSISTENCY-001"
    assert (
        dashboard_cases[0]["governance_status"]
        == "PENDING_DPO_GRC"
    )

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 1,
        "approved": 0,
        "blocked": 0,
        "approval_records": 0,
    }

    # ---------------------------------------------------------
    # 4. FastAPI must read the SAME runtime state.
    # ---------------------------------------------------------

    application = make_app()
    client = TestClient(application)

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

    # ---------------------------------------------------------
    # 5. API case list must contain the same case.
    # ---------------------------------------------------------

    cases_response = client.get(
        "/api/privacy/governance/cases",
    )

    assert cases_response.status_code == 200

    cases = cases_response.json()

    assert len(cases) == 1

    assert cases[0]["case_id"] == "CASE-CONSISTENCY-001"
    assert cases[0]["title"] == "New learner processing"
    assert cases[0]["trigger_type"] == "NEW_PROCESSING"
    assert cases[0]["validation_status"] == "PASS"
    assert cases[0]["governance_status"] == "PENDING_DPO_GRC"

    # ---------------------------------------------------------
    # 6. API detail must resolve the same case.
    # ---------------------------------------------------------

    detail_response = client.get(
        "/api/privacy/governance/cases/CASE-CONSISTENCY-001",
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["case_id"] == "CASE-CONSISTENCY-001"
    assert detail["governance_status"] == "PENDING_DPO_GRC"
    assert detail["validation_status"] == "PASS"

    assert detail["trigger"]["type"] == "NEW_PROCESSING"
    assert detail["trigger"]["source"] == "Processing Registry"

    assert detail["approval_history"] == []

    # ---------------------------------------------------------
    # 7. Record DPO approval through the application service.
    # ---------------------------------------------------------

    dpo_record = composition.case_service.approve(
        case_id="CASE-CONSISTENCY-001",
        change_id="PCR-CONSISTENCY-001",
        approval_id="APR-CONSISTENCY-DPO-001",
        reviewer="DPO Reviewer",
        role="DPO",
        comment="DPO review completed.",
    )

    assert dpo_record.decision.value == "APPROVED"

    # DPO approval alone is not enough because GRC is required.

    assert (
        composition.case_registry.get(
            "CASE-CONSISTENCY-001",
        ).governance_status
        == "PENDING_DPO_GRC"
    )

    # ---------------------------------------------------------
    # 8. Record GRC approval.
    # ---------------------------------------------------------

    grc_record = composition.case_service.approve(
        case_id="CASE-CONSISTENCY-001",
        change_id="PCR-CONSISTENCY-001",
        approval_id="APR-CONSISTENCY-GRC-001",
        reviewer="GRC Reviewer",
        role="GRC",
        comment="GRC review completed.",
    )

    assert grc_record.decision.value == "APPROVED"

    # ---------------------------------------------------------
    # 9. Runtime must now be APPROVED.
    # ---------------------------------------------------------

    case = composition.case_registry.get(
        "CASE-CONSISTENCY-001",
    )

    change = composition.change_registry.get(
        "PCR-CONSISTENCY-001",
    )

    assert case.governance_status == "APPROVED"
    assert case.final_decision == "APPROVED"
    assert case.final_decision_at is not None

    assert change.status == PrivacyChangeStatus.APPROVED

    # ---------------------------------------------------------
    # 10. Dashboard must see APPROVED state.
    # ---------------------------------------------------------

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 1,
        "blocked": 0,
        "approval_records": 2,
    }

    # ---------------------------------------------------------
    # 11. API must see the same APPROVED state.
    # ---------------------------------------------------------

    summary_response = client.get(
        "/api/privacy/governance/summary",
    )

    assert summary_response.status_code == 200

    assert summary_response.json() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 1,
        "blocked": 0,
        "approval_records": 2,
    }

    # ---------------------------------------------------------
    # 12. API detail must expose both approval records.
    # ---------------------------------------------------------

    detail_response = client.get(
        "/api/privacy/governance/cases/CASE-CONSISTENCY-001",
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["governance_status"] == "APPROVED"
    assert detail["final_decision"] == "APPROVED"

    history = detail["approval_history"]

    assert len(history) == 2

    assert history[0]["approval_id"] == "APR-CONSISTENCY-DPO-001"
    assert history[0]["reviewer"] == "DPO Reviewer"
    assert history[0]["role"] == "DPO"
    assert history[0]["decision"] == "APPROVED"

    assert history[1]["approval_id"] == "APR-CONSISTENCY-GRC-001"
    assert history[1]["reviewer"] == "GRC Reviewer"
    assert history[1]["role"] == "GRC"
    assert history[1]["decision"] == "APPROVED"


def test_runtime_and_api_share_blocked_state_after_validation_failure():
    """
    Prove that validation failure propagates consistently through:

        Runtime → Case Registry → Dashboard → FastAPI
    """

    composition = get_privacy_governance_composition()

    # ---------------------------------------------------------
    # 1. Process a NEW_PROCESSING with validation failure.
    # ---------------------------------------------------------

    result = composition.flow_service.process_new_processing(
        make_change(
            change_id="PCR-CONSISTENCY-BLOCKED-001",
        ),
        automated_validation_passed=False,
        case_id="CASE-CONSISTENCY-BLOCKED-001",
        trigger_source="Processing Registry",
    )

    # ---------------------------------------------------------
    # 2. Runtime state must be BLOCKED.
    # ---------------------------------------------------------

    assert result.change.status == PrivacyChangeStatus.BLOCKED

    assert result.case.case_id == "CASE-CONSISTENCY-BLOCKED-001"
    assert result.case.validation_status == "FAIL"
    assert result.case.governance_status == "BLOCKED"

    # ---------------------------------------------------------
    # 3. Shared registries must contain BLOCKED state.
    # ---------------------------------------------------------

    assert (
        composition.change_registry.get(
            "PCR-CONSISTENCY-BLOCKED-001",
        ).status
        == PrivacyChangeStatus.BLOCKED
    )

    assert (
        composition.case_registry.get(
            "CASE-CONSISTENCY-BLOCKED-001",
        ).governance_status
        == "BLOCKED"
    )

    # ---------------------------------------------------------
    # 4. Dashboard must expose BLOCKED state.
    # ---------------------------------------------------------

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 0,
        "blocked": 1,
        "approval_records": 0,
    }

    # ---------------------------------------------------------
    # 5. FastAPI must expose the same BLOCKED state.
    # ---------------------------------------------------------

    application = make_app()
    client = TestClient(application)

    summary_response = client.get(
        "/api/privacy/governance/summary",
    )

    assert summary_response.status_code == 200

    assert summary_response.json() == {
        "total_cases": 1,
        "pending": 0,
        "approved": 0,
        "blocked": 1,
        "approval_records": 0,
    }

    # ---------------------------------------------------------
    # 6. API case list must expose the blocked case.
    # ---------------------------------------------------------

    cases_response = client.get(
        "/api/privacy/governance/cases",
    )

    assert cases_response.status_code == 200

    cases = cases_response.json()

    assert len(cases) == 1

    assert cases[0]["case_id"] == "CASE-CONSISTENCY-BLOCKED-001"
    assert cases[0]["validation_status"] == "FAIL"
    assert cases[0]["governance_status"] == "BLOCKED"

    # ---------------------------------------------------------
    # 7. API detail must expose blocked state and no approvals.
    # ---------------------------------------------------------

    detail_response = client.get(
        "/api/privacy/governance/cases/"
        "CASE-CONSISTENCY-BLOCKED-001",
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["case_id"] == "CASE-CONSISTENCY-BLOCKED-001"
    assert detail["validation_status"] == "FAIL"
    assert detail["governance_status"] == "BLOCKED"
    assert detail["approval_history"] == []