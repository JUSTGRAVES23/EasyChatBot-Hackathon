"""
EasyChatBot AI Operations Center dashboard service tests.

Validates the read-only dashboard contract used by the
Operations Center.

Coverage:

- system confidence;
- monitoring status;
- active providers;
- active escalations;
- pending approvals;
- approved escalations;
- rejected escalations;
- pending notifications;
- total escalation counts.

The dashboard service must not modify workflow state.

Confidence model:

- 100 when there are no escalations;
- subtract 15 points per active escalation;
- pending approval is informational and is not
  penalised a second time;
- confidence cannot fall below 0.
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

from app.application.provider_management.operations_center_dashboard_service import (
    ActiveProvider,
    MonitoringStatus,
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
        approved_at=(
            datetime(
                2026,
                8,
                14,
                15,
                minute,
                tzinfo=timezone.utc,
            )
            if status
            == EscalationWorkflowStatus.APPROVED
            else None
        ),
        rejected_at=(
            datetime(
                2026,
                8,
                14,
                15,
                minute,
                tzinfo=timezone.utc,
            )
            if status
            == EscalationWorkflowStatus.REJECTED
            else None
        ),
        decision_reason=(
            "Operations decision recorded."
            if status
            in (
                EscalationWorkflowStatus.APPROVED,
                EscalationWorkflowStatus.REJECTED,
            )
            else None
        ),
    )


def create_service() -> (
    tuple[
        OperationsCenterDashboardService,
        InMemoryEscalationWorkflowRepository,
    ]
):
    """
    Create a dashboard service and repository.
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

    return dashboard_service, repository


def create_active_providers() -> tuple[
    ActiveProvider,
    ...,
]:
    """
    Create deterministic active provider data.
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


def test_empty_operations_center_is_healthy() -> None:
    """
    Validate the initial healthy dashboard.
    """

    service, _ = create_service()

    dashboard = service.build_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    assert (
        dashboard.system_confidence
        == 100.0
    )

    assert (
        dashboard.monitoring_status
        == MonitoringStatus.HEALTHY
    )

    assert (
        dashboard.active_escalations
        == 0
    )

    assert (
        dashboard.pending_approvals
        == 0
    )

    assert (
        dashboard.approved_escalations
        == 0
    )

    assert (
        dashboard.rejected_escalations
        == 0
    )

    assert (
        dashboard.pending_notifications
        == 0
    )

    assert (
        dashboard.total_escalations
        == 0
    )


def test_dashboard_exposes_active_providers() -> None:
    """
    Validate provider information reaches the dashboard.
    """

    service, _ = create_service()

    providers = create_active_providers()

    dashboard = service.build_dashboard(
        active_providers=providers
    )

    assert (
        dashboard.active_providers
        == providers
    )

    assert len(
        dashboard.active_providers
    ) == 3

    assert (
        dashboard.active_providers[0]
        .provider
        == "openai"
    )

    assert (
        dashboard.active_providers[1]
        .provider
        == "gemini"
    )

    assert (
        dashboard.active_providers[2]
        .provider
        == "ollama"
    )


def test_pending_approval_creates_incident_state() -> None:
    """
    Validate dashboard behaviour when human approval
    is required.
    """

    service, repository = create_service()

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

    dashboard = service.build_dashboard(
        active_providers=()
    )

    assert (
        dashboard.pending_approvals
        == 1
    )

    assert (
        dashboard.active_escalations
        == 1
    )

    assert (
        dashboard.monitoring_status
        == MonitoringStatus.INCIDENT
    )

    assert (
        dashboard.total_escalations
        == 1
    )


def test_pending_notification_is_active_escalation() -> None:
    """
    Validate that a notification awaiting delivery is
    still considered active.
    """

    service, repository = create_service()

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

    dashboard = service.build_dashboard(
        active_providers=()
    )

    assert (
        dashboard.pending_notifications
        == 1
    )

    assert (
        dashboard.active_escalations
        == 1
    )

    assert (
        dashboard.monitoring_status
        == MonitoringStatus.INCIDENT
    )


def test_approved_and_rejected_escalations_are_not_active() -> None:
    """
    Validate terminal workflow states do not count as
    active escalations.
    """

    service, repository = create_service()

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

    dashboard = service.build_dashboard(
        active_providers=()
    )

    assert (
        dashboard.active_escalations
        == 0
    )

    assert (
        dashboard.approved_escalations
        == 1
    )

    assert (
        dashboard.rejected_escalations
        == 1
    )

    assert (
        dashboard.total_escalations
        == 2
    )

    assert (
        dashboard.monitoring_status
        == MonitoringStatus.HEALTHY
    )


def test_dashboard_confidence_decreases_with_active_escalation() -> None:
    """
    Validate deterministic operational confidence scoring.

    One active escalation:

        100 - 15 = 85

    Pending approval does not receive an additional
    penalty because it is already represented by the
    active escalation.
    """

    service, repository = create_service()

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

    dashboard = service.build_dashboard(
        active_providers=()
    )

    assert (
        dashboard.system_confidence
        == 85.0
    )


def test_dashboard_confidence_never_goes_below_zero() -> None:
    """
    Validate confidence lower bound.
    """

    service, repository = create_service()

    for index in range(1, 20):
        repository.save(
            create_workflow(
                escalation_id=(
                    f"esc-{index:03d}"
                ),
                status=(
                    EscalationWorkflowStatus
                    .AWAITING_APPROVAL
                ),
                minute=(
                    30 + index
                ),
            )
        )

    dashboard = service.build_dashboard(
        active_providers=()
    )

    assert (
        dashboard.system_confidence
        == 0.0
    )


def test_dashboard_confidence_is_capped_at_one_hundred() -> None:
    """
    Validate confidence upper bound.
    """

    service, _ = create_service()

    dashboard = service.build_dashboard(
        active_providers=()
    )

    assert (
        dashboard.system_confidence
        <= 100.0
    )


def test_multiple_workflow_states_are_aggregated() -> None:
    """
    Validate the complete dashboard aggregation.

    Active workflows:

        1 pending notification
        2 awaiting approval

    Therefore:

        active escalations = 3

    Confidence:

        100 - (3 * 15) = 55
    """

    service, repository = create_service()

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

    repository.save(
        create_workflow(
            escalation_id="esc-003",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=32,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-004",
            status=(
                EscalationWorkflowStatus
                .APPROVED
            ),
            minute=33,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-005",
            status=(
                EscalationWorkflowStatus
                .REJECTED
            ),
            minute=34,
        )
    )

    dashboard = service.build_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    assert (
        dashboard.pending_notifications
        == 1
    )

    assert (
        dashboard.pending_approvals
        == 2
    )

    assert (
        dashboard.active_escalations
        == 3
    )

    assert (
        dashboard.approved_escalations
        == 1
    )

    assert (
        dashboard.rejected_escalations
        == 1
    )

    assert (
        dashboard.total_escalations
        == 5
    )

    assert (
        dashboard.monitoring_status
        == MonitoringStatus.INCIDENT
    )

    assert (
        dashboard.system_confidence
        == 55.0
    )


def test_none_active_providers_are_rejected() -> None:
    """
    Validate required provider input.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Active providers cannot be None.",
    ):
        service.build_dashboard(
            active_providers=None,  # type: ignore[arg-type]
        )


def test_dashboard_is_read_only() -> None:
    """
    Validate that dashboard generation does not modify
    persisted workflow state.
    """

    service, repository = create_service()

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

    service.build_dashboard(
        active_providers=(
            create_active_providers()
        )
    )

    after = repository.get_all()

    assert before == after