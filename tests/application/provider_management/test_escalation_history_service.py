"""
EasyChatBot AI Operations Center escalation history tests.

Validates the read-only application contract used by
the Operations Center.

Coverage:

- complete escalation history;
- individual workflow retrieval;
- status filtering;
- pending approval;
- approved history;
- rejected history;
- pending notification;
- status counts;
- pending approval detection.

The service must not mutate workflow state.
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


def create_workflow(
    *,
    escalation_id: str,
    status: EscalationWorkflowStatus,
    minute: int,
) -> EscalationWorkflow:
    """
    Create deterministic workflow history data.
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
            == EscalationWorkflowStatus
            .APPROVED
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
            == EscalationWorkflowStatus
            .REJECTED
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
        EscalationHistoryService,
        InMemoryEscalationWorkflowRepository,
    ]
):
    """
    Create a history service and repository.
    """

    repository = (
        InMemoryEscalationWorkflowRepository()
    )

    service = EscalationHistoryService(
        repository=repository
    )

    return service, repository


def populate_repository(
    repository: InMemoryEscalationWorkflowRepository,
) -> None:
    """
    Populate deterministic escalation history.
    """

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
                .APPROVED
            ),
            minute=32,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-004",
            status=(
                EscalationWorkflowStatus
                .REJECTED
            ),
            minute=33,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-005",
            status=(
                EscalationWorkflowStatus
                .AWAITING_APPROVAL
            ),
            minute=34,
        )
    )


def test_list_history_returns_all_workflows() -> None:
    """
    Validate complete history retrieval.
    """

    service, repository = create_service()

    populate_repository(repository)

    history = service.list_history()

    assert len(history) == 5

    assert [
        workflow.escalation_id
        for workflow in history
    ] == [
        "esc-001",
        "esc-002",
        "esc-003",
        "esc-004",
        "esc-005",
    ]


def test_get_returns_requested_workflow() -> None:
    """
    Validate individual workflow retrieval.
    """

    service, repository = create_service()

    populate_repository(repository)

    workflow = service.get(
        "esc-003"
    )

    assert workflow is not None

    assert (
        workflow.escalation_id
        == "esc-003"
    )

    assert (
        workflow.status
        == EscalationWorkflowStatus
        .APPROVED
    )


def test_get_returns_none_for_unknown_workflow() -> None:
    """
    Validate unknown workflow behaviour.
    """

    service, repository = create_service()

    populate_repository(repository)

    assert (
        service.get("esc-404")
        is None
    )


def test_get_rejects_empty_escalation_id() -> None:
    """
    Validate workflow identity.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Escalation ID cannot be empty.",
    ):
        service.get("   ")


def test_list_by_status_filters_correctly() -> None:
    """
    Validate generic status filtering.
    """

    service, repository = create_service()

    populate_repository(repository)

    awaiting = service.list_by_status(
        EscalationWorkflowStatus
        .AWAITING_APPROVAL
    )

    assert len(awaiting) == 2

    assert {
        workflow.escalation_id
        for workflow in awaiting
    } == {
        "esc-002",
        "esc-005",
    }


def test_list_by_status_rejects_none() -> None:
    """
    Validate required status input.
    """

    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Workflow status cannot be None.",
    ):
        service.list_by_status(
            None,  # type: ignore[arg-type]
        )


def test_list_pending_approval() -> None:
    """
    Validate Operations Center pending approval view.
    """

    service, repository = create_service()

    populate_repository(repository)

    pending = (
        service.list_pending_approval()
    )

    assert len(pending) == 2

    assert all(
        workflow.status
        == EscalationWorkflowStatus
        .AWAITING_APPROVAL
        for workflow in pending
    )


def test_list_approved() -> None:
    """
    Validate approved escalation history.
    """

    service, repository = create_service()

    populate_repository(repository)

    approved = service.list_approved()

    assert len(approved) == 1

    assert (
        approved[0].escalation_id
        == "esc-003"
    )

    assert (
        approved[0].status
        == EscalationWorkflowStatus
        .APPROVED
    )


def test_list_rejected() -> None:
    """
    Validate rejected escalation history.
    """

    service, repository = create_service()

    populate_repository(repository)

    rejected = service.list_rejected()

    assert len(rejected) == 1

    assert (
        rejected[0].escalation_id
        == "esc-004"
    )

    assert (
        rejected[0].status
        == EscalationWorkflowStatus
        .REJECTED
    )


def test_list_pending_notification() -> None:
    """
    Validate pending notification view.
    """

    service, repository = create_service()

    populate_repository(repository)

    pending = (
        service.list_pending_notification()
    )

    assert len(pending) == 1

    assert (
        pending[0].escalation_id
        == "esc-001"
    )

    assert (
        pending[0].status
        == EscalationWorkflowStatus
        .PENDING_NOTIFICATION
    )


def test_count_by_status() -> None:
    """
    Validate dashboard status counts.
    """

    service, repository = create_service()

    populate_repository(repository)

    counts = service.count_by_status()

    assert (
        counts[
            EscalationWorkflowStatus
            .PENDING_NOTIFICATION
        ]
        == 1
    )

    assert (
        counts[
            EscalationWorkflowStatus
            .AWAITING_APPROVAL
        ]
        == 2
    )

    assert (
        counts[
            EscalationWorkflowStatus
            .APPROVED
        ]
        == 1
    )

    assert (
        counts[
            EscalationWorkflowStatus
            .REJECTED
        ]
        == 1
    )


def test_count_by_status_includes_zero_counts() -> None:
    """
    Validate that all lifecycle statuses are represented
    even when no workflows exist for a status.
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

    counts = service.count_by_status()

    assert (
        counts[
            EscalationWorkflowStatus
            .APPROVED
        ]
        == 1
    )

    assert (
        counts[
            EscalationWorkflowStatus
            .PENDING_NOTIFICATION
        ]
        == 0
    )

    assert (
        counts[
            EscalationWorkflowStatus
            .AWAITING_APPROVAL
        ]
        == 0
    )

    assert (
        counts[
            EscalationWorkflowStatus
            .REJECTED
        ]
        == 0
    )


def test_has_pending_approval_returns_true() -> None:
    """
    Validate pending approval detection.
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

    assert (
        service.has_pending_approval()
        is True
    )


def test_has_pending_approval_returns_false() -> None:
    """
    Validate absence of pending approvals.
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

    assert (
        service.has_pending_approval()
        is False
    )


def test_history_service_is_read_only() -> None:
    """
    Validate that querying history does not change
    repository state.
    """

    service, repository = create_service()

    populate_repository(repository)

    before = repository.get_all()

    service.list_history()
    service.list_pending_approval()
    service.list_approved()
    service.list_rejected()
    service.list_pending_notification()
    service.count_by_status()
    service.has_pending_approval()

    after = repository.get_all()

    assert before == after