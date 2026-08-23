"""
EasyChatBot AI Operations Center dashboard facade tests.

Validates the presentation-facing dashboard contract.

The facade must:

- expose JSON-safe primitive values;
- serialize monitoring status;
- serialize active providers;
- preserve dashboard counts;
- preserve system confidence;
- avoid exposing internal Enum/dataclass objects;
- remain read-only.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.escalation_history_service import (
    EscalationHistoryService,
)

from app.application.provider_management.escalation_workflow_repository import (
    InMemoryEscalationWorkflowRepository,
)

from app.application.provider_management.escalation_workflow_service import (
    EscalationWorkflow,
    EscalationWorkflowStatus,
)

from app.application.provider_management.operations_center_dashboard_facade import (
    OperationsCenterDashboardFacade,
)

from app.application.provider_management.operations_center_dashboard_service import (
    ActiveProvider,
    OperationsCenterDashboardService,
)


def create_workflow(
    *,
    escalation_id: str,
    status: EscalationWorkflowStatus,
    minute: int,
) -> EscalationWorkflow:
    """
    Create deterministic workflow data.
    """

    return EscalationWorkflow(
        escalation_id=escalation_id,
        status=status,
        created_at=datetime(
            2026,
            8,
            14,
            14,
            minute,
            tzinfo=timezone.utc,
        ),
        notification_recipient=(
            "operations@example.com"
            if status
            != EscalationWorkflowStatus
            .PENDING_NOTIFICATION
            else None
        ),
        notification_subject=(
            "EasyChatBot AI Operations Escalation"
            if status
            != EscalationWorkflowStatus
            .PENDING_NOTIFICATION
            else None
        ),
        approved_at=None,
        rejected_at=None,
        decision_reason=None,
    )


def create_service() -> (
    tuple[
        OperationsCenterDashboardFacade,
        InMemoryEscalationWorkflowRepository,
    ]
):
    """
    Create the facade with its application dependencies.
    """

    repository = (
        InMemoryEscalationWorkflowRepository()
    )

    history_service = (
        EscalationHistoryService(
            repository=repository
        )
    )

    dashboard_service = (
        OperationsCenterDashboardService(
            history_service=history_service
        )
    )

    facade = OperationsCenterDashboardFacade(
        dashboard_service=dashboard_service
    )

    return facade, repository


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
        ActiveProvider(
            provider="ollama",
            model="gemma4",
            capabilities=(
                "internal_experiments",
            ),
        ),
    )


def test_facade_returns_healthy_dashboard() -> None:
    """
    Validate the basic healthy Operations Center response.
    """

    facade, _ = create_service()

    result = facade.get_dashboard(
        active_providers=(
            create_active_providers()
        )
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


def test_facade_serializes_active_providers() -> None:
    """
    Validate provider serialization.
    """

    facade, _ = create_service()

    result = facade.get_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    providers = result[
        "active_providers"
    ]

    assert isinstance(
        providers,
        list,
    )

    assert len(providers) == 3

    assert providers[0] == {
        "provider": "openai",
        "model": "gpt-5-mini",
        "capabilities": [
            "conversation",
            "reasoning",
        ],
        "active": True,
    }

    assert providers[1] == {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "capabilities": [
            "summarisation",
        ],
        "active": True,
    }

    assert providers[2] == {
        "provider": "ollama",
        "model": "gemma4",
        "capabilities": [
            "internal_experiments",
        ],
        "active": True,
    }


def test_facade_serializes_monitoring_status_as_string() -> None:
    """
    Validate that internal Enum objects are not exposed.
    """

    facade, repository = create_service()

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=30,
        )
    )

    result = facade.get_dashboard(
        active_providers=()
    )

    assert (
        result["monitoring_status"]
        == "incident"
    )

    assert isinstance(
        result["monitoring_status"],
        str,
    )


def test_facade_serializes_active_escalation_state() -> None:
    """
    Validate dashboard information needed by the
    Operations Center landing page.
    """

    facade, repository = create_service()

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            status=(
                EscalationWorkflowStatus
                .PENDING_NOTIFICATION
            ),
            minute=30,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-002",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=31,
        )
    )

    result = facade.get_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    assert (
        result["active_escalations"]
        == 2
    )

    assert (
        result["pending_notifications"]
        == 1
    )

    assert (
        result["pending_approvals"]
        == 1
    )

    assert (
        result["total_escalations"]
        == 2
    )

    assert (
        result["system_confidence"]
        == 70.0
    )


def test_facade_serializes_terminal_workflows() -> None:
    """
    Validate approved and rejected history.
    """

    facade, repository = create_service()

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            status=(
                EscalationWorkflowStatus
                .APPROVED
            ),
            minute=30,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-002",
            status=(
                EscalationWorkflowStatus
                .REJECTED
            ),
            minute=31,
        )
    )

    result = facade.get_dashboard(
        active_providers=()
    )

    assert (
        result["active_escalations"]
        == 0
    )

    assert (
        result["approved_escalations"]
        == 1
    )

    assert (
        result["rejected_escalations"]
        == 1
    )

    assert (
        result["total_escalations"]
        == 2
    )

    assert (
        result["system_confidence"]
        == 100.0
    )

    assert (
        result["monitoring_status"]
        == "healthy"
    )


def test_facade_result_is_json_safe() -> None:
    """
    Validate that the complete dashboard result consists
    only of JSON-compatible primitive/container values.

    This deliberately avoids importing a JSON framework so
    the application layer remains infrastructure-independent.
    """

    facade, repository = create_service()

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=30,
        )
    )

    result = facade.get_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    def assert_json_safe(
        value: object,
    ) -> None:
        if value is None:
            return

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return

        if isinstance(value, list):
            for item in value:
                assert_json_safe(item)
            return

        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(
                    key,
                    str,
                )
                assert_json_safe(item)
            return

        raise AssertionError(
            "Dashboard contains a non-JSON-safe "
            f"value: {type(value)!r}"
        )

    assert_json_safe(result)


def test_facade_does_not_expose_internal_workflow_objects() -> None:
    """
    Validate that the presentation boundary returns plain
    dictionaries rather than internal workflow objects.
    """

    facade, repository = create_service()

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=30,
        )
    )

    result = facade.get_dashboard(
        active_providers=()
    )

    assert isinstance(
        result,
        dict,
    )

    assert all(
        not isinstance(
            value,
            EscalationWorkflow,
        )
        for value in result.values()
    )


def test_facade_is_read_only() -> None:
    """
    Validate that generating the dashboard does not modify
    repository state.
    """

    facade, repository = create_service()

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=30,
        )
    )

    before = repository.get_all()

    facade.get_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    after = repository.get_all()

    assert before == after


def test_none_dashboard_service_is_rejected() -> None:
    """
    Validate dependency injection.
    """

    with pytest.raises(
        ValueError,
        match=(
            "Operations Center dashboard service "
            "cannot be None."
        ),
    ):
        OperationsCenterDashboardFacade(
            dashboard_service=None,  # type: ignore[arg-type]
        )


def test_none_active_providers_are_rejected() -> None:
    """
    Validate required provider input.
    """

    facade, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Active providers cannot be None.",
    ):
        facade.get_dashboard(
            active_providers=None,  # type: ignore[arg-type]
        )