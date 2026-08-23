"""
EasyChatBot AI Operations Center escalation workflow tests.

Validates the human-in-the-loop lifecycle:

Escalation
    |
    v
PENDING_NOTIFICATION
    |
    v
AWAITING_APPROVAL
    |
    +------------------+
    |                  |
    v                  v
 APPROVED           REJECTED

Approval records a human decision only.

It does NOT execute provider changes,
modify Runtime routing, or perform failover.
"""

from datetime import datetime, timezone

import pytest

from app.application.provider_management.email_notification_adapter import (
    InMemoryEmailNotificationAdapter,
)

from app.application.provider_management.escalation_notification_service import (
    EscalationNotificationService,
)

from app.application.provider_management.escalation_workflow_service import (
    EscalationWorkflowService,
    EscalationWorkflowStatus,
)

from app.application.provider_management.models import (
    EscalationSeverity,
    EscalationType,
    ProviderEscalation,
)


def create_escalation() -> ProviderEscalation:
    """
    Create a deterministic escalation.
    """

    return ProviderEscalation(
        escalation_id="esc-001",
        escalation_type=(
            EscalationType.PROVIDER_FAILURE
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="openai",
        capability="conversation",
        message=(
            "Provider openai is currently unavailable."
        ),
        recommendation=(
            "Review alternative providers for "
            "conversation workloads."
        ),
        created_at=datetime(
            2026,
            8,
            14,
            14,
            34,
            tzinfo=timezone.utc,
        ),
    )


def create_service() -> EscalationWorkflowService:
    """
    Create a workflow service using the in-memory
    notification adapter.
    """

    adapter = (
        InMemoryEmailNotificationAdapter()
    )

    notification_service = (
        EscalationNotificationService(
            email_adapter=adapter
        )
    )

    return EscalationWorkflowService(
        notification_service=(
            notification_service
        )
    )


def test_workflow_starts_pending_notification() -> None:
    """
    Validate initial workflow state.
    """

    service = create_service()

    workflow = service.create_workflow(
        escalation=create_escalation()
    )

    assert (
        workflow.escalation_id
        == "esc-001"
    )

    assert (
        workflow.status
        == EscalationWorkflowStatus
        .PENDING_NOTIFICATION
    )

    assert (
        workflow.notification_recipient
        is None
    )

    assert (
        workflow.approved_at
        is None
    )

    assert (
        workflow.rejected_at
        is None
    )


def test_notification_moves_workflow_to_awaiting_approval() -> None:
    """
    Validate notification preparation and workflow
    transition.
    """

    service = create_service()

    escalation = create_escalation()

    service.create_workflow(
        escalation=escalation
    )

    notification = (
        service.prepare_notification(
            escalation=escalation,
            recipient="operations@example.com",
        )
    )

    assert (
        notification.recipient
        == "operations@example.com"
    )

    workflow = service.get_workflow(
        "esc-001"
    )

    assert workflow is not None

    assert (
        workflow.status
        == EscalationWorkflowStatus
        .AWAITING_APPROVAL
    )

    assert (
        workflow.notification_recipient
        == "operations@example.com"
    )

    assert (
        workflow.notification_subject
        is not None
    )


def test_notification_can_create_workflow_automatically() -> None:
    """
    Validate that notification preparation can initialise
    a missing workflow.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    workflow = service.get_workflow(
        "esc-001"
    )

    assert workflow is not None

    assert (
        workflow.status
        == EscalationWorkflowStatus
        .AWAITING_APPROVAL
    )


def test_human_can_approve_escalation() -> None:
    """
    Validate human approval.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    approved = service.approve(
        escalation_id="esc-001",
        reason=(
            "Operations reviewed the incident "
            "and approved the recommendation."
        ),
    )

    assert (
        approved.status
        == EscalationWorkflowStatus
        .APPROVED
    )

    assert (
        approved.approved_at
        is not None
    )

    assert (
        approved.rejected_at
        is None
    )

    assert (
        approved.decision_reason
        == (
            "Operations reviewed the incident "
            "and approved the recommendation."
        )
    )


def test_human_can_reject_escalation() -> None:
    """
    Validate human rejection.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    rejected = service.reject(
        escalation_id="esc-001",
        reason=(
            "Operations determined that the "
            "provider issue is transient."
        ),
    )

    assert (
        rejected.status
        == EscalationWorkflowStatus
        .REJECTED
    )

    assert (
        rejected.rejected_at
        is not None
    )

    assert (
        rejected.approved_at
        is None
    )

    assert (
        rejected.decision_reason
        == (
            "Operations determined that the "
            "provider issue is transient."
        )
    )


def test_approval_requires_awaiting_approval_state() -> None:
    """
    Validate that approval cannot happen before
    notification workflow state.
    """

    service = create_service()

    service.create_workflow(
        escalation=create_escalation()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Escalation must be awaiting approval "
            "before it can be approved."
        ),
    ):
        service.approve(
            escalation_id="esc-001",
            reason="Approved.",
        )


def test_rejection_requires_awaiting_approval_state() -> None:
    """
    Validate that rejection cannot happen before
    notification workflow state.
    """

    service = create_service()

    service.create_workflow(
        escalation=create_escalation()
    )

    with pytest.raises(
        ValueError,
        match=(
            "Escalation must be awaiting approval "
            "before it can be rejected."
        ),
    ):
        service.reject(
            escalation_id="esc-001",
            reason="Rejected.",
        )


def test_approval_requires_reason() -> None:
    """
    Validate approval audit reason.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    with pytest.raises(
        ValueError,
        match="Approval reason cannot be empty.",
    ):
        service.approve(
            escalation_id="esc-001",
            reason="   ",
        )


def test_rejection_requires_reason() -> None:
    """
    Validate rejection audit reason.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    with pytest.raises(
        ValueError,
        match="Rejection reason cannot be empty.",
    ):
        service.reject(
            escalation_id="esc-001",
            reason="   ",
        )


def test_approved_workflow_cannot_be_approved_twice() -> None:
    """
    Validate workflow state immutability after approval.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    service.approve(
        escalation_id="esc-001",
        reason="Approved after review.",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Escalation must be awaiting approval "
            "before it can be approved."
        ),
    ):
        service.approve(
            escalation_id="esc-001",
            reason="Second approval.",
        )


def test_rejected_workflow_cannot_be_approved() -> None:
    """
    Validate that rejection is terminal for the current
    workflow lifecycle.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    service.reject(
        escalation_id="esc-001",
        reason="Rejected by Operations.",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Escalation must be awaiting approval "
            "before it can be approved."
        ),
    ):
        service.approve(
            escalation_id="esc-001",
            reason="Approve later.",
        )


def test_approved_workflow_cannot_be_rejected() -> None:
    """
    Validate that approval is terminal for the current
    workflow lifecycle.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    service.approve(
        escalation_id="esc-001",
        reason="Approved by Operations.",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Escalation must be awaiting approval "
            "before it can be rejected."
        ),
    ):
        service.reject(
            escalation_id="esc-001",
            reason="Reject later.",
        )


def test_unknown_workflow_is_rejected() -> None:
    """
    Validate missing workflow handling.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Escalation workflow not found: esc-404"
        ),
    ):
        service.approve(
            escalation_id="esc-404",
            reason="Approved.",
        )


def test_none_escalation_is_rejected() -> None:
    """
    Validate required escalation input.
    """

    service = create_service()

    with pytest.raises(
        ValueError,
        match="Provider escalation cannot be None.",
    ):
        service.create_workflow(
            escalation=None,  # type: ignore[arg-type]
        )


def test_empty_escalation_id_is_rejected() -> None:
    """
    Validate escalation identity.
    """

    service = create_service()

    escalation = ProviderEscalation(
        escalation_id="   ",
        escalation_type=(
            EscalationType.PROVIDER_FAILURE
        ),
        severity=(
            EscalationSeverity.HIGH
        ),
        provider="openai",
        capability="conversation",
        message="Provider unavailable.",
        recommendation="Review alternatives.",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    with pytest.raises(
        ValueError,
        match="Escalation ID cannot be empty.",
    ):
        service.create_workflow(
            escalation=escalation
        )


def test_workflow_list_contains_created_workflows() -> None:
    """
    Validate workflow retrieval.
    """

    service = create_service()

    first = create_escalation()

    second = ProviderEscalation(
        escalation_id="esc-002",
        escalation_type=(
            EscalationType.LATENCY_DEGRADATION
        ),
        severity=(
            EscalationSeverity.MEDIUM
        ),
        provider="gemini",
        capability="summarisation",
        message="Latency degraded.",
        recommendation="Review provider performance.",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    service.create_workflow(
        escalation=first
    )

    service.create_workflow(
        escalation=second
    )

    workflows = service.list_workflows()

    assert len(workflows) == 2

    assert {
        workflow.escalation_id
        for workflow in workflows
    } == {
        "esc-001",
        "esc-002",
    }


def test_notification_then_approval_preserves_audit_data() -> None:
    """
    Validate that notification metadata remains available
    after a human approval decision.
    """

    service = create_service()

    escalation = create_escalation()

    service.prepare_notification(
        escalation=escalation,
        recipient="operations@example.com",
    )

    approved = service.approve(
        escalation_id="esc-001",
        reason="Approved after Operations review.",
    )

    assert (
        approved.notification_recipient
        == "operations@example.com"
    )

    assert (
        approved.notification_subject
        is not None
    )

    assert (
        approved.approved_at
        is not None
    )

    assert (
        approved.decision_reason
        == "Approved after Operations review."
    )