from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
)
from app.application.privacy.privacy_governance_api_sync import (
    PrivacyGovernanceAPIEvidenceSync,
)
from app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
)
from app.application.privacy.privacy_governance_dashboard_api import (
    PrivacyGovernanceDashboardAPI,
)


# ============================================================================
# PRIVACY GOVERNANCE API
# ============================================================================
#
# This is the single canonical privacy governance router.
#
# READ:
#   GET  /api/privacy/governance/summary
#   GET  /api/privacy/governance/status-chart
#   GET  /api/privacy/governance/cases
#   GET  /api/privacy/governance/cases/{case_id}
#
# HUMAN GOVERNANCE:
#   POST /api/privacy/governance/cases/{case_id}/approve
#   POST /api/privacy/governance/cases/{case_id}/reject
#   POST /api/privacy/governance/cases/{case_id}/request-changes
#
# BETA / DEVELOPMENT:
#   POST /api/privacy/governance/demo/create-case
#
# Existing tests and application integrations intentionally import:
#
#     from app.api.privacy_governance import router
#
# Therefore all privacy governance endpoints remain attached to this
# canonical router.
# ============================================================================

router = APIRouter(
    prefix="/api/privacy/governance",
    tags=["privacy-governance"],
)


class PrivacyGovernanceDecisionRequest(BaseModel):
    """Explicit human governance decision request."""

    change_id: str = Field(
        min_length=1,
    )

    approval_id: str = Field(
        min_length=1,
    )

    reviewer: str = Field(
        min_length=1,
    )

    role: str = Field(
        min_length=1,
    )

    comment: str = Field(
        min_length=1,
    )


class PrivacyGovernanceDemoCaseRequest(BaseModel):
    """Controlled Beta/demo governance case creation request.

    This endpoint exists only for development and demonstration.

    Production case creation must use the governed application workflow
    rather than this demo adapter.
    """

    case_id: str = Field(
        default="CASE-E2E-001",
        min_length=1,
    )

    change_id: str = Field(
        default="PCR-E2E-001",
        min_length=1,
    )


def _composition():
    """Resolve the process-wide governance composition."""

    return get_privacy_governance_composition()


def _dashboard_api() -> PrivacyGovernanceDashboardAPI:
    """Resolve the read-only governance dashboard API."""

    composition = _composition()

    return PrivacyGovernanceDashboardAPI(
        dashboard_service=composition.dashboard_service,
    )


def _evidence_sync() -> PrivacyGovernanceAPIEvidenceSync:
    """Resolve the API-to-Excel evidence synchronization adapter."""

    composition = _composition()

    return PrivacyGovernanceAPIEvidenceSync(
        case_service=composition.case_service,
    )


def _require_decision_role(
    role: str,
) -> str:
    """Validate the explicitly submitted governance role."""

    normalized = role.strip().upper()

    if normalized not in {
        "DPO",
        "GRC",
    }:
        raise HTTPException(
            status_code=400,
            detail="role must be DPO or GRC.",
        )

    return normalized


def _decision_response(
    *,
    case_id: str,
    record: object,
) -> dict[str, object]:
    """Return decision evidence, refreshed case state, and Excel sync status."""

    dashboard = _dashboard_api()

    try:
        case = dashboard.get_case_detail(
            case_id,
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    evidence = _evidence_sync().sync_decision(
        case_id,
    )

    return {
        "case": case,
        "approval_record": jsonable_encoder(
            record,
        ),
        "excel_sync": {
            "status": evidence.status,
            "workbook_path": evidence.workbook_path,
            "error": evidence.error,
        },
    }


# ============================================================================
# READ-ONLY GOVERNANCE ENDPOINTS
# ============================================================================


@router.get("/summary")
def get_summary() -> dict[str, int]:
    """Return current privacy governance dashboard KPIs."""

    return _dashboard_api().get_summary()


@router.get("/status-chart")
def get_status_chart() -> list[dict[str, object]]:
    """Return current governance status chart data."""

    return list(
        _dashboard_api().get_status_chart(),
    )


@router.get("/cases")
def get_cases() -> list[dict[str, object]]:
    """Return current governance case rows."""

    return list(
        _dashboard_api().get_cases(),
    )


@router.get("/cases/{case_id}")
def get_case_detail(
    case_id: str,
) -> dict[str, object]:
    """Return complete read-only governance case detail."""

    try:
        return _dashboard_api().get_case_detail(
            case_id,
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


# ============================================================================
# EXPLICIT HUMAN GOVERNANCE DECISION ENDPOINTS
# ============================================================================
#
# IMPORTANT:
#
# These endpoints intentionally use `router`.
#
# Do NOT create a second `decision_router` here.
#
# The existing tests directly import and register `router`.
# ============================================================================


@router.post(
    "/cases/{case_id}/approve",
)
def approve_case(
    case_id: str,
    request: PrivacyGovernanceDecisionRequest,
) -> dict[str, object]:
    """Record one explicit human approval."""

    role = _require_decision_role(
        request.role,
    )

    composition = _composition()

    try:
        record = composition.case_service.approve(
            case_id=case_id,
            change_id=request.change_id,
            approval_id=request.approval_id,
            reviewer=request.reviewer.strip(),
            role=role,
            comment=request.comment.strip(),
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return _decision_response(
        case_id=case_id,
        record=record,
    )


@router.post(
    "/cases/{case_id}/reject",
)
def reject_case(
    case_id: str,
    request: PrivacyGovernanceDecisionRequest,
) -> dict[str, object]:
    """Record an explicit human rejection."""

    role = _require_decision_role(
        request.role,
    )

    composition = _composition()

    try:
        record = composition.case_service.reject(
            case_id=case_id,
            change_id=request.change_id,
            approval_id=request.approval_id,
            reviewer=request.reviewer.strip(),
            role=role,
            comment=request.comment.strip(),
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return _decision_response(
        case_id=case_id,
        record=record,
    )


@router.post(
    "/cases/{case_id}/request-changes",
)
def request_case_changes(
    case_id: str,
    request: PrivacyGovernanceDecisionRequest,
) -> dict[str, object]:
    """Record an explicit human request-for-changes decision."""

    role = _require_decision_role(
        request.role,
    )

    composition = _composition()

    try:
        record = composition.case_service.request_changes(
            case_id=case_id,
            change_id=request.change_id,
            approval_id=request.approval_id,
            reviewer=request.reviewer.strip(),
            role=role,
            comment=request.comment.strip(),
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return _decision_response(
        case_id=case_id,
        record=record,
    )


# ============================================================================
# CONTROLLED BETA / DEVELOPMENT ENDPOINT
# ============================================================================


@router.post(
    "/demo/create-case",
)
def create_demo_case(
    request: PrivacyGovernanceDemoCaseRequest | None = None,
) -> dict[str, object]:
    """Create a controlled Beta demonstration governance case.

    Development/demo only.

    Production case creation must use the governed application workflow.
    """

    composition = _composition()

    demo_request = (
        request
        if request is not None
        else PrivacyGovernanceDemoCaseRequest()
    )

    case_id = demo_request.case_id.strip()
    change_id = demo_request.change_id.strip()

    if not case_id:
        raise HTTPException(
            status_code=400,
            detail="case_id cannot be blank.",
        )

    if not change_id:
        raise HTTPException(
            status_code=400,
            detail="change_id cannot be blank.",
        )

    change = PrivacyChange(
        change_id=change_id,
        title="New learner data processing",
        description=(
            "Beta demonstration of a new privacy-impacting "
            "learner processing activity."
        ),
        risk=PrivacyChangeRisk.MEDIUM,
        dpo_required=True,
        grc_required=True,
    )

    try:
        result = composition.flow_service.process_new_processing(
            change,
            automated_validation_passed=True,
            case_id=case_id,
            trigger_source="Processing Registry",
        )

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    evidence = _evidence_sync().sync_case(
        result.case.case_id,
    )

    return {
        "case_id": result.case.case_id,
        "change_id": result.change.change_id,
        "validation_status": result.case.validation_status,
        "governance_status": result.case.governance_status,
        "excel_sync": {
            "status": evidence.status,
            "workbook_path": evidence.workbook_path,
            "error": evidence.error,
        },
    }


__all__ = [
    "PrivacyGovernanceDecisionRequest",
    "PrivacyGovernanceDemoCaseRequest",
    "router",
]
