from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.privacy_governance import router
from app.application.privacy.privacy_governance_case import (
    PrivacyGovernanceCase,
    PrivacyTriggerType,
)
from app.application.privacy.privacy_governance_composition import (
    create_privacy_governance_composition,
)


EXPECTED_READ_PATHS = {
    "/api/privacy/governance/summary",
    "/api/privacy/governance/status-chart",
    "/api/privacy/governance/cases",
    "/api/privacy/governance/cases/{case_id}",
}


EXPECTED_DECISION_PATHS = {
    "/api/privacy/governance/cases/{case_id}/approve",
    "/api/privacy/governance/cases/{case_id}/reject",
    "/api/privacy/governance/cases/{case_id}/request-changes",
}


EXPECTED_DEMO_PATHS = {
    "/api/privacy/governance/demo/create-case",
}


def make_app() -> FastAPI:
    """Create a minimal FastAPI application for API adapter tests."""

    app = FastAPI()
    app.include_router(router)

    return app


def router_paths() -> set[str]:
    """Return all concrete paths declared by the privacy governance router."""

    return {
        route.path
        for route in router.routes
        if getattr(route, "path", None)
    }


def router_get_paths() -> set[str]:
    """Return only GET paths declared by the privacy governance router."""

    return {
        route.path
        for route in router.routes
        if (
            getattr(route, "path", None)
            and "GET" in getattr(route, "methods", set())
        )
    }


def router_post_paths() -> set[str]:
    """Return only POST paths declared by the privacy governance router."""

    return {
        route.path
        for route in router.routes
        if (
            getattr(route, "path", None)
            and "POST" in getattr(route, "methods", set())
        )
    }


def test_api_router_exposes_four_read_endpoints():
    """
    Verify the privacy governance router declares exactly the four
    read-only GET endpoints.

    Decision and development/demo POST endpoints are intentionally excluded
    from this assertion because they are not read-only endpoints.
    """

    assert router_get_paths() == EXPECTED_READ_PATHS


def test_api_router_exposes_human_decision_endpoints():
    """Verify the explicit human governance decision endpoints exist."""

    post_paths = router_post_paths()

    assert EXPECTED_DECISION_PATHS.issubset(
        post_paths
    )


def test_api_router_exposes_controlled_demo_endpoint():
    """Verify the controlled Beta/demo endpoint exists."""

    post_paths = router_post_paths()

    assert EXPECTED_DEMO_PATHS.issubset(
        post_paths
    )


def test_api_router_is_registered_in_fastapi_application():
    """
    Verify the application contains the privacy governance router.

    The installed FastAPI version stores included routers internally,
    so registration is verified through the router's original_router
    reference when necessary.
    """

    app = make_app()

    included_router = next(
        (
            route
            for route in app.routes
            if getattr(route, "original_router", None) is router
        ),
        None,
    )

    assert included_router is not None


def test_composition_shares_registry_instances_with_dashboard_service():
    composition = create_privacy_governance_composition()

    assert (
        composition.dashboard_service._cases
        is composition.case_registry
    )

    assert (
        composition.dashboard_service._approvals
        is composition.approval_registry
    )


def test_summary_and_chart_are_read_only_and_return_expected_shape():
    composition = create_privacy_governance_composition()

    composition.case_registry.register(
        PrivacyGovernanceCase(
            case_id="CASE-001",
            title="New processing",
            summary="A controlled processing change.",
            trigger_type=PrivacyTriggerType.NEW_PROCESSING,
            triggered_at=datetime.now(timezone.utc),
            trigger_source="Processing Registry",
            governance_status="PENDING_DPO_GRC",
        )
    )

    assert composition.dashboard_service.summary() == {
        "total_cases": 1,
        "pending": 1,
        "approved": 0,
        "blocked": 0,
        "approval_records": 0,
    }

    assert composition.dashboard_service.status_chart() == (
        {
            "status": "Pending DPO/GRC",
            "count": 1,
        },
        {
            "status": "Approved",
            "count": 0,
        },
        {
            "status": "Rejected / Blocked",
            "count": 0,
        },
    )


def test_case_list_contains_stable_identifier_and_trigger():
    composition = create_privacy_governance_composition()

    composition.case_registry.register(
        PrivacyGovernanceCase(
            case_id="CASE-002",
            title="Data mapping change",
            summary="A controlled data-map change.",
            trigger_type=PrivacyTriggerType.DATA_MAPPING_CHANGE,
            triggered_at=datetime.now(timezone.utc),
            trigger_source="Data Processing Map",
            risk="HIGH",
            validation_status="PASS",
            email_status="SENT",
        )
    )

    row = composition.dashboard_service.case_list()[0]

    assert row["case_id"] == "CASE-002"
    assert row["trigger_type"] == "DATA_MAPPING_CHANGE"
    assert row["validation_status"] == "PASS"
    assert row["email_status"] == "SENT"


def test_unknown_case_is_controlled():
    composition = create_privacy_governance_composition()

    try:
        composition.dashboard_service.case_detail(
            "DOES-NOT-EXIST"
        )
    except KeyError as exc:
        assert "Governance case not found" in str(exc)
    else:
        raise AssertionError(
            "Unknown case did not raise KeyError"
        )


def test_fastapi_unknown_case_returns_404():
    app = make_app()
    client = TestClient(app)

    response = client.get(
        "/api/privacy/governance/cases/DOES-NOT-EXIST"
    )

    assert response.status_code == 404
