"""
EasyChatBot AI Operations Center dashboard API tests.

Validates the thin API adapter boundary.

The API adapter must:

- delegate to the dashboard facade;
- expose the facade result unchanged;
- reject invalid provider input;
- reject a missing facade dependency;
- avoid introducing business logic;
- remain read-only.
"""

from unittest.mock import Mock

import pytest

from app.application.provider_management.operations_center_dashboard_facade import (
    OperationsCenterDashboardFacade,
)

from app.application.provider_management.operations_center_dashboard_service import (
    ActiveProvider,
)

from app.interfaces.provider_management.operations_center_dashboard_api import (
    OperationsCenterDashboardAPI,
)


def create_active_providers() -> tuple[
    ActiveProvider,
    ...
]:
    """
    Create deterministic provider data.
    """

    return (
        ActiveProvider(
            provider="openai",
            model="gpt-5-mini",
            capabilities=(
                "conversation",
                "reasoning",
            ),
        ),
        ActiveProvider(
            provider="gemini",
            model="gemini-2.5-flash",
            capabilities=(
                "summarisation",
            ),
        ),
    )


def create_facade_mock() -> Mock:
    """
    Create a facade test double.
    """

    facade = Mock(
        spec=OperationsCenterDashboardFacade
    )

    facade.get_dashboard.return_value = {
        "system_confidence": 85.0,
        "monitoring_status": "incident",
        "active_providers": [
            {
                "provider": "openai",
                "model": "gpt-5-mini",
                "capabilities": [
                    "conversation",
                    "reasoning",
                ],
                "active": True,
            }
        ],
        "active_escalations": 1,
        "pending_approvals": 1,
        "approved_escalations": 0,
        "rejected_escalations": 0,
        "pending_notifications": 0,
        "total_escalations": 1,
    }

    return facade


def test_api_delegates_to_facade() -> None:
    """
    Validate that dashboard generation is delegated to the
    application facade.
    """

    facade = create_facade_mock()

    api = OperationsCenterDashboardAPI(
        facade=facade
    )

    providers = create_active_providers()

    result = api.get_dashboard(
        active_providers=providers
    )

    facade.get_dashboard.assert_called_once_with(
        active_providers=providers,
    )

    assert result == (
        facade.get_dashboard.return_value
    )


def test_api_returns_facade_result_unchanged() -> None:
    """
    Validate that the API adapter does not transform or
    alter the application contract.
    """

    facade = create_facade_mock()

    expected = {
        "system_confidence": 100.0,
        "monitoring_status": "healthy",
        "active_providers": [],
        "active_escalations": 0,
        "pending_approvals": 0,
        "approved_escalations": 0,
        "rejected_escalations": 0,
        "pending_notifications": 0,
        "total_escalations": 0,
    }

    facade.get_dashboard.return_value = (
        expected
    )

    api = OperationsCenterDashboardAPI(
        facade=facade
    )

    result = api.get_dashboard(
        active_providers=()
    )

    assert result is expected


def test_api_rejects_none_active_providers() -> None:
    """
    Validate required provider input.
    """

    facade = create_facade_mock()

    api = OperationsCenterDashboardAPI(
        facade=facade
    )

    with pytest.raises(
        ValueError,
        match="Active providers cannot be None.",
    ):
        api.get_dashboard(
            active_providers=None,  # type: ignore[arg-type]
        )

    facade.get_dashboard.assert_not_called()


def test_api_rejects_none_facade() -> None:
    """
    Validate dependency injection.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operations Center dashboard facade "
            "cannot be None."
        ),
    ):
        OperationsCenterDashboardAPI(
            facade=None,  # type: ignore[arg-type]
        )


def test_api_does_not_add_business_logic() -> None:
    """
    Validate that the API simply exposes the facade contract.

    The API must not calculate confidence, classify incidents,
    or interpret escalation state itself.
    """

    facade = create_facade_mock()

    facade.get_dashboard.return_value = {
        "system_confidence": 55.0,
        "monitoring_status": "incident",
        "active_providers": [],
        "active_escalations": 3,
        "pending_approvals": 2,
        "approved_escalations": 1,
        "rejected_escalations": 1,
        "pending_notifications": 1,
        "total_escalations": 5,
    }

    api = OperationsCenterDashboardAPI(
        facade=facade
    )

    result = api.get_dashboard(
        active_providers=()
    )

    assert result[
        "system_confidence"
    ] == 55.0

    assert result[
        "active_escalations"
    ] == 3

    assert result[
        "pending_approvals"
    ] == 2

    assert result[
        "monitoring_status"
    ] == "incident"

    facade.get_dashboard.assert_called_once()


def test_api_is_read_only() -> None:
    """
    Validate that the API adapter only reads through the
    facade and has no mutation operation.
    """

    facade = create_facade_mock()

    api = OperationsCenterDashboardAPI(
        facade=facade
    )

    result = api.get_dashboard(
        active_providers=()
    )

    assert result is not None

    assert not hasattr(
        api,
        "approve",
    )

    assert not hasattr(
        api,
        "reject",
    )

    assert not hasattr(
        api,
        "update_provider",
    )

    assert not hasattr(
        api,
        "change_routing",
    )