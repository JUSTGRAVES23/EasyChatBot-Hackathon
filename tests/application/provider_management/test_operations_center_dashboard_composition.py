"""
EasyChatBot AI Operations Center dashboard composition tests.

Validates the composition root for the Operations Center.

The composition must assemble:

Provider Health Monitor
        |
        v
Operations Center Provider Service
        |
        v
Dashboard Service
        |
        v
Dashboard Facade
        |
        v
Dashboard API

The composition root must:

- construct the dashboard API successfully;
- preserve dependency boundaries;
- avoid constructing dependencies inside the router;
- expose a usable read-only dashboard API;
- preserve the existing Dashboard API contract.
"""

from app.application.provider_management.operations_center_dashboard_api import (
    OperationsCenterDashboardAPI,
)

from app.application.provider_management.operations_center_dashboard_composition import (
    create_operations_center_dashboard_api,
)


def create_empty_dashboard(
    api: OperationsCenterDashboardAPI,
) -> dict:
    """
    Build a deterministic empty dashboard using the current
    Dashboard API contract.

    Provider health integration is intentionally tested in
    a separate vertical slice.
    """

    return api.get_dashboard(
        active_providers=()
    )


def test_dashboard_composition_creates_api() -> None:
    """
    Validate that the composition root creates the dashboard
    API successfully.
    """

    api = (
        create_operations_center_dashboard_api()
    )

    assert isinstance(
        api,
        OperationsCenterDashboardAPI,
    )


def test_dashboard_composition_returns_usable_api() -> None:
    """
    Validate that the composed API can build a dashboard.

    No provider observations have been submitted yet, so the
    explicit provider input is empty.

    This test verifies the composition root without changing
    the existing Dashboard API contract.
    """

    api = (
        create_operations_center_dashboard_api()
    )

    result = create_empty_dashboard(
        api
    )

    assert isinstance(
        result,
        dict,
    )

    assert (
        result["system_confidence"]
        == 100.0
    )

    assert (
        result["monitoring_status"]
        == "healthy"
    )

    assert (
        result["active_providers"]
        == []
    )

    assert (
        result["active_escalations"]
        == 0
    )

    assert (
        result["pending_approvals"]
        == 0
    )

    assert (
        result["approved_escalations"]
        == 0
    )

    assert (
        result["rejected_escalations"]
        == 0
    )

    assert (
        result["pending_notifications"]
        == 0
    )

    assert (
        result["total_escalations"]
        == 0
    )


def test_dashboard_composition_is_read_only() -> None:
    """
    Validate that composing the dashboard does not itself
    perform provider operations or create operational state.
    """

    first_api = (
        create_operations_center_dashboard_api()
    )

    second_api = (
        create_operations_center_dashboard_api()
    )

    first_result = (
        create_empty_dashboard(
            first_api
        )
    )

    second_result = (
        create_empty_dashboard(
            second_api
        )
    )

    assert (
        first_result
        == second_result
    )


def test_dashboard_composition_creates_independent_instances() -> None:
    """
    Validate that composition creates independent application
    instances rather than sharing mutable state accidentally.
    """

    first_api = (
        create_operations_center_dashboard_api()
    )

    second_api = (
        create_operations_center_dashboard_api()
    )

    assert (
        first_api is not second_api
    )