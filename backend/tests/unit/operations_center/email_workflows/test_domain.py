from datetime import datetime, timezone

import pytest

from app.application.operations_center.email_workflows.domain import (
    EmailWorkflowDefinition,
    EmailWorkflowLifecycle,
    EmailWorkflowType,
)


def make_workflow(
    *,
    workflow_type=EmailWorkflowType.SCHEDULED,
    lifecycle=EmailWorkflowLifecycle.ACTIVE,
    schedule="0 8 * * *",
):
    now = datetime.now(timezone.utc)

    return EmailWorkflowDefinition(
        workflow_id="test.workflow",
        name="Test Workflow",
        description="Test email workflow",
        workflow_type=workflow_type,
        lifecycle=lifecycle,
        owner="test",
        trigger="scheduled",
        schedule=schedule,
        template_id="test-template",
        version=1,
        created_at=now,
        updated_at=now,
    )


def test_scheduled_workflow_requires_schedule():
    with pytest.raises(ValueError, match="must define a schedule"):
        make_workflow(schedule=None)


def test_non_scheduled_workflow_cannot_define_schedule():
    with pytest.raises(
        ValueError,
        match="Only SCHEDULED workflows",
    ):
        make_workflow(
            workflow_type=EmailWorkflowType.EVENT_DRIVEN,
            schedule="0 8 * * *",
        )


def test_active_scheduled_workflow_can_pause():
    workflow = make_workflow()

    assert workflow.can_pause() is True


def test_event_driven_workflow_cannot_pause():
    workflow = make_workflow(
        workflow_type=EmailWorkflowType.EVENT_DRIVEN,
        schedule=None,
    )

    assert workflow.can_pause() is False


def test_paused_workflow_can_resume():
    workflow = make_workflow(
        lifecycle=EmailWorkflowLifecycle.PAUSED,
    )

    assert workflow.can_resume() is True


def test_disabled_workflow_can_enable():
    workflow = make_workflow(
        lifecycle=EmailWorkflowLifecycle.DISABLED,
    )

    assert workflow.can_enable() is True


def test_archived_workflow_cannot_be_archived_again():
    workflow = make_workflow(
        lifecycle=EmailWorkflowLifecycle.ARCHIVED,
    )

    assert workflow.can_archive() is False


def test_lifecycle_change_is_immutable_and_increments_version():
    workflow = make_workflow()

    updated = workflow.with_lifecycle(
        EmailWorkflowLifecycle.PAUSED
    )

    assert workflow.lifecycle is EmailWorkflowLifecycle.ACTIVE
    assert updated.lifecycle is EmailWorkflowLifecycle.PAUSED
    assert updated.version == 2
    assert updated.workflow_id == workflow.workflow_id
