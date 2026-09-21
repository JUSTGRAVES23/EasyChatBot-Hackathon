from datetime import datetime, timezone

import pytest

from app.application.operations_center.email_workflows.domain import (
    EmailWorkflowDefinition,
    EmailWorkflowLifecycle,
    EmailWorkflowType,
)
from app.application.operations_center.email_workflows.in_memory_registry import (
    InMemoryEmailWorkflowRegistry,
)
from app.application.operations_center.email_workflows.lifecycle_service import (
    EmailWorkflowLifecycleService,
)


def make_workflow(
    workflow_id: str = "workflow.test",
    *,
    workflow_type: EmailWorkflowType = EmailWorkflowType.SCHEDULED,
    lifecycle: EmailWorkflowLifecycle = EmailWorkflowLifecycle.ACTIVE,
):
    now = datetime.now(timezone.utc)

    return EmailWorkflowDefinition(
        workflow_id=workflow_id,
        name="Test Workflow",
        description="Lifecycle test",
        workflow_type=workflow_type,
        lifecycle=lifecycle,
        owner="test",
        trigger="scheduled",
        schedule="0 8 * * *"
        if workflow_type is EmailWorkflowType.SCHEDULED
        else None,
        template_id="test-template",
        version=1,
        created_at=now,
        updated_at=now,
    )


def service_with(workflow):
    registry = InMemoryEmailWorkflowRegistry()
    registry.create(workflow)
    return EmailWorkflowLifecycleService(registry), registry


def test_pause_active_scheduled_workflow():
    service, registry = service_with(make_workflow())

    result = service.pause("workflow.test")

    assert result.lifecycle is EmailWorkflowLifecycle.PAUSED
    assert registry.get("workflow.test").lifecycle is EmailWorkflowLifecycle.PAUSED


def test_resume_paused_workflow():
    service, _ = service_with(
        make_workflow(
            lifecycle=EmailWorkflowLifecycle.PAUSED,
        )
    )

    result = service.resume("workflow.test")

    assert result.lifecycle is EmailWorkflowLifecycle.ACTIVE


def test_disable_active_workflow():
    service, _ = service_with(make_workflow())

    result = service.disable("workflow.test")

    assert result.lifecycle is EmailWorkflowLifecycle.DISABLED


def test_enable_disabled_workflow():
    service, _ = service_with(
        make_workflow(
            lifecycle=EmailWorkflowLifecycle.DISABLED,
        )
    )

    result = service.enable("workflow.test")

    assert result.lifecycle is EmailWorkflowLifecycle.ACTIVE


def test_archive_active_workflow():
    service, _ = service_with(make_workflow())

    result = service.archive("workflow.test")

    assert result.lifecycle is EmailWorkflowLifecycle.ARCHIVED


def test_archive_paused_workflow():
    service, _ = service_with(
        make_workflow(
            lifecycle=EmailWorkflowLifecycle.PAUSED,
        )
    )

    result = service.archive("workflow.test")

    assert result.lifecycle is EmailWorkflowLifecycle.ARCHIVED


def test_event_driven_workflow_cannot_be_paused():
    service, _ = service_with(
        make_workflow(
            workflow_type=EmailWorkflowType.EVENT_DRIVEN,
        )
    )

    with pytest.raises(
        ValueError,
        match="cannot be paused",
    ):
        service.pause("workflow.test")


def test_archived_workflow_is_terminal():
    service, _ = service_with(
        make_workflow(
            lifecycle=EmailWorkflowLifecycle.ARCHIVED,
        )
    )

    with pytest.raises(ValueError):
        service.enable("workflow.test")

    with pytest.raises(ValueError):
        service.pause("workflow.test")

    with pytest.raises(ValueError):
        service.archive("workflow.test")


def test_missing_workflow_fails():
    registry = InMemoryEmailWorkflowRegistry()
    service = EmailWorkflowLifecycleService(registry)

    with pytest.raises(
        KeyError,
        match="Workflow not found",
    ):
        service.pause("does.not.exist")


def test_invalid_resume_fails():
    service, _ = service_with(make_workflow())

    with pytest.raises(
        ValueError,
        match="cannot be resumed",
    ):
        service.resume("workflow.test")


def test_invalid_enable_fails():
    service, _ = service_with(make_workflow())

    with pytest.raises(
        ValueError,
        match="cannot be enabled",
    ):
        service.enable("workflow.test")


def test_invalid_pause_from_disabled_fails():
    service, _ = service_with(
        make_workflow(
            lifecycle=EmailWorkflowLifecycle.DISABLED,
        )
    )

    with pytest.raises(
        ValueError,
        match="cannot be paused",
    ):
        service.pause("workflow.test")
