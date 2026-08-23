"""
EasyChatBot AI Operations Center escalation workflow
repository tests.

Validates:

EscalationWorkflowService
        |
        v
EscalationWorkflowRepository
        |
        v
In-Memory Persistence
        |
        v
Escalation History

The repository does not:

- make business decisions;
- send notifications;
- approve escalations;
- modify Runtime routing;
- execute provider changes.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.escalation_workflow_repository import (
    InMemoryEscalationWorkflowRepository,
)

from app.application.provider_management.escalation_workflow_service import (
    EscalationWorkflow,
    EscalationWorkflowStatus,
)


def create_workflow(
    *,
    escalation_id: str = "esc-001",
    status: EscalationWorkflowStatus = (
        EscalationWorkflowStatus.PENDING_NOTIFICATION
    ),
    created_at: datetime | None = None,
) -> EscalationWorkflow:
    """
    Create a deterministic workflow record.
    """

    if created_at is None:
        created_at = datetime(
            2026,
            8,
            14,
            14,
            30,
            tzinfo=timezone.utc,
        )

    return EscalationWorkflow(
        escalation_id=escalation_id,
        status=status,
        created_at=created_at,
        notification_recipient=None,
        notification_subject=None,
        approved_at=None,
        rejected_at=None,
        decision_reason=None,
    )


def create_repository() -> (
    InMemoryEscalationWorkflowRepository
):
    """
    Create a fresh repository.
    """

    return InMemoryEscalationWorkflowRepository()


def test_workflow_can_be_saved_and_retrieved() -> None:
    """
    Validate basic persistence and retrieval.
    """

    repository = create_repository()

    workflow = create_workflow()

    repository.save(workflow)

    retrieved = repository.get(
        "esc-001"
    )

    assert retrieved is not None

    assert (
        retrieved.escalation_id
        == "esc-001"
    )

    assert (
        retrieved.status
        == EscalationWorkflowStatus
        .PENDING_NOTIFICATION
    )

    assert (
        retrieved.created_at
        == workflow.created_at
    )


def test_saving_existing_workflow_replaces_previous_state() -> None:
    """
    Validate workflow state updates.
    """

    repository = create_repository()

    created_at = datetime(
        2026,
        8,
        14,
        14,
        30,
        tzinfo=timezone.utc,
    )

    pending = create_workflow(
        escalation_id="esc-001",
        status=(
            EscalationWorkflowStatus
            .PENDING_NOTIFICATION
        ),
        created_at=created_at,
    )

    repository.save(pending)

    approved = EscalationWorkflow(
        escalation_id="esc-001",
        status=(
            EscalationWorkflowStatus
            .APPROVED
        ),
        created_at=created_at,
        notification_recipient=(
            "operations@example.com"
        ),
        notification_subject=(
            "EasyChatBot AI Operations Escalation"
        ),
        approved_at=datetime(
            2026,
            8,
            14,
            14,
            40,
            tzinfo=timezone.utc,
        ),
        rejected_at=None,
        decision_reason=(
            "Approved by Operations."
        ),
    )

    repository.save(approved)

    retrieved = repository.get(
        "esc-001"
    )

    assert retrieved is not None

    assert (
        retrieved.status
        == EscalationWorkflowStatus
        .APPROVED
    )

    assert (
        retrieved.notification_recipient
        == "operations@example.com"
    )

    assert (
        retrieved.decision_reason
        == "Approved by Operations."
    )

    assert (
        retrieved.approved_at
        is not None
    )


def test_missing_workflow_returns_none() -> None:
    """
    Validate missing workflow lookup.
    """

    repository = create_repository()

    result = repository.get(
        "esc-404"
    )

    assert result is None


def test_empty_escalation_id_is_rejected_on_get() -> None:
    """
    Validate workflow identity on retrieval.
    """

    repository = create_repository()

    with pytest.raises(
        ValueError,
        match="Escalation ID cannot be empty.",
    ):
        repository.get("   ")


def test_none_workflow_is_rejected() -> None:
    """
    Validate required persistence input.
    """

    repository = create_repository()

    with pytest.raises(
        ValueError,
        match=(
            "Escalation workflow cannot be None."
        ),
    ):
        repository.save(
            None,  # type: ignore[arg-type]
        )


def test_empty_escalation_id_is_rejected_on_save() -> None:
    """
    Validate workflow identity during persistence.
    """

    repository = create_repository()

    workflow = create_workflow(
        escalation_id="   "
    )

    with pytest.raises(
        ValueError,
        match="Escalation ID cannot be empty.",
    ):
        repository.save(workflow)


def test_multiple_workflows_can_be_persisted() -> None:
    """
    Validate multiple independent workflow records.
    """

    repository = create_repository()

    repository.save(
        create_workflow(
            escalation_id="esc-001"
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-002"
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-003"
        )
    )

    workflows = repository.get_all()

    assert len(workflows) == 3

    assert {
        workflow.escalation_id
        for workflow in workflows
    } == {
        "esc-001",
        "esc-002",
        "esc-003",
    }


def test_workflows_are_returned_in_creation_order() -> None:
    """
    Validate deterministic history ordering.
    """

    repository = create_repository()

    first_time = datetime(
        2026,
        8,
        14,
        14,
        30,
        tzinfo=timezone.utc,
    )

    second_time = datetime(
        2026,
        8,
        14,
        14,
        31,
        tzinfo=timezone.utc,
    )

    third_time = datetime(
        2026,
        8,
        14,
        14,
        32,
        tzinfo=timezone.utc,
    )

    repository.save(
        create_workflow(
            escalation_id="esc-003",
            created_at=third_time,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-001",
            created_at=first_time,
        )
    )

    repository.save(
        create_workflow(
            escalation_id="esc-002",
            created_at=second_time,
        )
    )

    workflows = repository.get_all()

    assert [
        workflow.escalation_id
        for workflow in workflows
    ] == [
        "esc-001",
        "esc-002",
        "esc-003",
    ]


def test_get_all_returns_empty_collection_initially() -> None:
    """
    Validate empty repository behaviour.
    """

    repository = create_repository()

    assert repository.get_all() == []


def test_notification_state_is_persisted() -> None:
    """
    Validate persistence of notification metadata.
    """

    repository = create_repository()

    created_at = datetime(
        2026,
        8,
        14,
        14,
        30,
        tzinfo=timezone.utc,
    )

    notification_time = datetime(
        2026,
        8,
        14,
        14,
        35,
        tzinfo=timezone.utc,
    )

    workflow = EscalationWorkflow(
        escalation_id="esc-001",
        status=(
            EscalationWorkflowStatus
            .AWAITING_APPROVAL
        ),
        created_at=created_at,
        notification_recipient=(
            "operations@example.com"
        ),
        notification_subject=(
            "EasyChatBot AI Operations Escalation"
        ),
        approved_at=None,
        rejected_at=None,
        decision_reason=None,
    )

    repository.save(workflow)

    retrieved = repository.get(
        "esc-001"
    )

    assert retrieved is not None

    assert (
        retrieved.status
        == EscalationWorkflowStatus
        .AWAITING_APPROVAL
    )

    assert (
        retrieved.notification_recipient
        == "operations@example.com"
    )

    assert (
        retrieved.notification_subject
        == "EasyChatBot AI Operations Escalation"
    )

    assert (
        retrieved.approved_at
        is None
    )

    assert (
        retrieved.rejected_at
        is None
    )

    # Keep the timestamp variable explicitly used so this
    # test documents the intended notification timeline.
    assert notification_time > created_at


def test_rejected_state_is_persisted() -> None:
    """
    Validate persistence of a human rejection decision.
    """

    repository = create_repository()

    created_at = datetime(
        2026,
        8,
        14,
        14,
        30,
        tzinfo=timezone.utc,
    )

    rejected_at = datetime(
        2026,
        8,
        14,
        14,
        42,
        tzinfo=timezone.utc,
    )

    workflow = EscalationWorkflow(
        escalation_id="esc-001",
        status=(
            EscalationWorkflowStatus
            .REJECTED
        ),
        created_at=created_at,
        notification_recipient=(
            "operations@example.com"
        ),
        notification_subject=(
            "EasyChatBot AI Operations Escalation"
        ),
        approved_at=None,
        rejected_at=rejected_at,
        decision_reason=(
            "Issue resolved without provider change."
        ),
    )

    repository.save(workflow)

    retrieved = repository.get(
        "esc-001"
    )

    assert retrieved is not None

    assert (
        retrieved.status
        == EscalationWorkflowStatus
        .REJECTED
    )

    assert (
        retrieved.rejected_at
        == rejected_at
    )

    assert (
        retrieved.decision_reason
        == (
            "Issue resolved without provider change."
        )
    )


def test_approved_state_is_persisted() -> None:
    """
    Validate persistence of a human approval decision.
    """

    repository = create_repository()

    created_at = datetime(
        2026,
        8,
        14,
        14,
        30,
        tzinfo=timezone.utc,
    )

    approved_at = datetime(
        2026,
        8,
        14,
        14,
        41,
        tzinfo=timezone.utc,
    )

    workflow = EscalationWorkflow(
        escalation_id="esc-001",
        status=(
            EscalationWorkflowStatus
            .APPROVED
        ),
        created_at=created_at,
        notification_recipient=(
            "operations@example.com"
        ),
        notification_subject=(
            "EasyChatBot AI Operations Escalation"
        ),
        approved_at=approved_at,
        rejected_at=None,
        decision_reason=(
            "Approved after provider review."
        ),
    )

    repository.save(workflow)

    retrieved = repository.get(
        "esc-001"
    )

    assert retrieved is not None

    assert (
        retrieved.status
        == EscalationWorkflowStatus
        .APPROVED
    )

    assert (
        retrieved.approved_at
        == approved_at
    )

    assert (
        retrieved.decision_reason
        == "Approved after provider review."
    )