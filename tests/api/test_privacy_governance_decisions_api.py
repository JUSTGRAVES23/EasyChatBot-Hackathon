from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.privacy_governance import router
from backend.app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
    reset_privacy_governance_composition_for_tests,
)
from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
)


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def seed_case() -> None:
    composition = get_privacy_governance_composition()

    composition.flow_service.process_new_processing(
        PrivacyChange(
            change_id="PCR-API-6G-001",
            title="6G API decision test",
            description="API decision integration test.",
            risk=PrivacyChangeRisk.MEDIUM,
            dpo_required=True,
            grc_required=True,
        ),
        automated_validation_passed=True,
        case_id="CASE-API-6G-001",
        trigger_source="Processing Registry",
    )


def setup_function() -> None:
    reset_privacy_governance_composition_for_tests()


def teardown_function() -> None:
    reset_privacy_governance_composition_for_tests()


def payload(role: str, approval_id: str) -> dict[str, str]:
    return {
        "change_id": "PCR-API-6G-001",
        "approval_id": approval_id,
        "reviewer": f"{role} Reviewer",
        "role": role,
        "comment": f"{role} reviewed the case.",
    }


def test_dpo_approval_is_recorded_and_case_remains_pending() -> None:
    seed_case()
    client = TestClient(make_app())

    response = client.post(
        "/api/privacy/governance/cases/CASE-API-6G-001/approve",
        json=payload("DPO", "APR-DPO-6G-001"),
    )

    assert response.status_code == 200
    body = response.json()

    assert body["case"]["governance_status"] == "PENDING_DPO_GRC"
    assert body["approval_record"]["decision"] == "APPROVED"


def test_dpo_and_grc_approvals_move_case_to_approved() -> None:
    seed_case()
    client = TestClient(make_app())

    first = client.post(
        "/api/privacy/governance/cases/CASE-API-6G-001/approve",
        json=payload("DPO", "APR-DPO-6G-002"),
    )
    assert first.status_code == 200

    second = client.post(
        "/api/privacy/governance/cases/CASE-API-6G-001/approve",
        json=payload("GRC", "APR-GRC-6G-002"),
    )

    assert second.status_code == 200
    assert second.json()["case"]["governance_status"] == "APPROVED"
    assert second.json()["case"]["final_decision"] == "APPROVED"

    summary = client.get(
        "/api/privacy/governance/summary"
    )

    assert summary.status_code == 200
    assert summary.json()["approval_records"] == 2
    assert summary.json()["approved"] == 1
    assert summary.json()["pending"] == 0


def test_rejection_blocks_case() -> None:
    seed_case()
    client = TestClient(make_app())

    response = client.post(
        "/api/privacy/governance/cases/CASE-API-6G-001/reject",
        json=payload("DPO", "APR-DPO-6G-003"),
    )

    assert response.status_code == 200
    assert response.json()["case"]["governance_status"] == "BLOCKED"
    assert response.json()["case"]["final_decision"] == "REJECTED"


def test_request_changes_blocks_case() -> None:
    seed_case()
    client = TestClient(make_app())

    response = client.post(
        "/api/privacy/governance/cases/CASE-API-6G-001/request-changes",
        json=payload("GRC", "APR-GRC-6G-004"),
    )

    assert response.status_code == 200
    assert response.json()["case"]["governance_status"] == "BLOCKED"
    assert response.json()["case"]["final_decision"] == "REQUEST_CHANGES"


def test_invalid_role_is_rejected() -> None:
    seed_case()
    client = TestClient(make_app())

    response = client.post(
        "/api/privacy/governance/cases/CASE-API-6G-001/approve",
        json=payload("ADMIN", "APR-ADMIN-6G-005"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "role must be DPO or GRC."


def test_unknown_case_is_controlled() -> None:
    client = TestClient(make_app())

    response = client.post(
        "/api/privacy/governance/cases/DOES-NOT-EXIST/approve",
        json=payload("DPO", "APR-UNKNOWN-001"),
    )

    assert response.status_code == 404
