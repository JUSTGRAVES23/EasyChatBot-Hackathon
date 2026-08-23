from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.privacy_governance import router
from backend.app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
    reset_privacy_governance_composition_for_tests,
)
from backend.app.application.privacy.privacy_governance_api_sync import (
    PrivacyGovernanceAPIEvidenceSync,
)
from backend.app.application.privacy.privacy_governance_excel_runtime_config import (
    get_privacy_governance_workbook_path,
)


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_api_decision_syncs_excel_after_dpo_approval(
    tmp_path: Path,
    monkeypatch,
):
    reset_privacy_governance_composition_for_tests()

    workbook = tmp_path / "tracker.xlsx"
    monkeypatch.setenv(
        "EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK",
        str(workbook),
    )

    client = TestClient(make_app())

    created = client.post(
        "/api/privacy/governance/demo/create-case"
    )

    assert created.status_code == 200
    assert created.json()["excel_sync"]["status"] == "SYNCED"

    response = client.post(
        "/api/privacy/governance/cases/CASE-E2E-001/approve",
        json={
            "change_id": "PCR-E2E-001",
            "approval_id": "APR-API-DPO-001",
            "reviewer": "DPO Reviewer",
            "role": "DPO",
            "comment": "DPO approval.",
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["case"]["governance_status"] == "PENDING_DPO_GRC"
    assert payload["excel_sync"]["status"] == "SYNCED"
    assert workbook.exists()


def test_api_dpo_plus_grc_produces_approved_excel_projection(
    tmp_path: Path,
    monkeypatch,
):
    reset_privacy_governance_composition_for_tests()

    workbook = tmp_path / "tracker.xlsx"
    monkeypatch.setenv(
        "EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK",
        str(workbook),
    )

    client = TestClient(make_app())

    assert client.post(
        "/api/privacy/governance/demo/create-case"
    ).status_code == 200

    dpo = client.post(
        "/api/privacy/governance/cases/CASE-E2E-001/approve",
        json={
            "change_id": "PCR-E2E-001",
            "approval_id": "APR-API-DPO-001",
            "reviewer": "DPO Reviewer",
            "role": "DPO",
            "comment": "DPO approval.",
        },
    )

    assert dpo.status_code == 200

    grc = client.post(
        "/api/privacy/governance/cases/CASE-E2E-001/approve",
        json={
            "change_id": "PCR-E2E-001",
            "approval_id": "APR-API-GRC-001",
            "reviewer": "GRC Reviewer",
            "role": "GRC",
            "comment": "GRC approval.",
        },
    )

    assert grc.status_code == 200
    payload = grc.json()

    assert payload["case"]["governance_status"] == "APPROVED"
    assert payload["excel_sync"]["status"] == "SYNCED"
    assert workbook.exists()


def test_api_rejection_and_request_changes_sync_excel(
    tmp_path: Path,
    monkeypatch,
):
    # Rejection lifecycle.
    reset_privacy_governance_composition_for_tests()

    workbook = tmp_path / "rejection.xlsx"
    monkeypatch.setenv(
        "EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK",
        str(workbook),
    )

    client = TestClient(make_app())

    assert client.post(
        "/api/privacy/governance/demo/create-case"
    ).status_code == 200

    response = client.post(
        "/api/privacy/governance/cases/CASE-E2E-001/reject",
        json={
            "change_id": "PCR-E2E-001",
            "approval_id": "APR-API-REJECT-001",
            "reviewer": "DPO Reviewer",
            "role": "DPO",
            "comment": "Rejected for testing.",
        },
    )

    assert response.status_code == 200
    assert response.json()["case"]["governance_status"] == "BLOCKED"
    assert response.json()["excel_sync"]["status"] == "SYNCED"

    # Request-changes lifecycle.
    reset_privacy_governance_composition_for_tests()

    workbook2 = tmp_path / "request-changes.xlsx"
    monkeypatch.setenv(
        "EASYCHATBOT_PRIVACY_GOVERNANCE_WORKBOOK",
        str(workbook2),
    )

    client = TestClient(make_app())

    assert client.post(
        "/api/privacy/governance/demo/create-case"
    ).status_code == 200

    response = client.post(
        "/api/privacy/governance/cases/CASE-E2E-001/request-changes",
        json={
            "change_id": "PCR-E2E-001",
            "approval_id": "APR-API-CHANGES-001",
            "reviewer": "GRC Reviewer",
            "role": "GRC",
            "comment": "Changes required.",
        },
    )

    assert response.status_code == 200
    assert response.json()["case"]["governance_status"] == "BLOCKED"
    assert response.json()["excel_sync"]["status"] == "SYNCED"
