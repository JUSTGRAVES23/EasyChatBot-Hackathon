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


def make_workflow(
    workflow_id: str = "workflow.test",
    *,
    lifecycle: EmailWorkflowLifecycle = EmailWorkflowLifecycle.ACTIVE,
) -> EmailWorkflowDefinition:
    now = datetime.now(timezone.utc)

    return EmailWorkflowDefinition(
        workflow_id=workflow_id,
        name=f"Workflow {workflow_id}",
        description="Registry test workflow",
        workflow_type=EmailWorkflowType.SCHEDULED,
        lifecycle=lifecycle,
        owner="test",
        trigger="scheduled",
        schedule="0 8 * * *",
        template_id="test-template",
        version=1,
        created_at=now,
        updated_at=now,
    )


def test_create_and_get_workflow():
    registry = InMemoryEmailWorkflowRegistry()
    workflow = make_workflow()

    created = registry.create(workflow)

    assert created == workflow
    assert registry.get("workflow.test") == workflow


def test_duplicate_workflow_id_is_rejected():
    registry = InMemoryEmailWorkflowRegistry()

    registry.create(make_workflow())

    with pytest.raises(
        ValueError,
        match="Workflow already exists",
    ):
        registry.create(make_workflow())


def test_missing_workflow_returns_none():
    registry = InMemoryEmailWorkflowRegistry()

    assert registry.get("does.not.exist") is None


def test_list_returns_workflows_in_deterministic_order():
    registry = InMemoryEmailWorkflowRegistry()

    registry.create(make_workflow("workflow.z"))
    registry.create(make_workflow("workflow.a"))

    workflows = registry.list()

    assert [workflow.workflow_id for workflow in workflows] == [
        "workflow.a",
        "workflow.z",
    ]


def test_update_existing_workflow():
    registry = InMemoryEmailWorkflowRegistry()

    workflow = make_workflow()
    registry.create(workflow)

    updated = workflow.with_lifecycle(
        EmailWorkflowLifecycle.PAUSED
    )

    result = registry.update(updated)

    assert result.lifecycle is EmailWorkflowLifecycle.PAUSED
    assert registry.get("workflow.test") == updated


def test_update_missing_workflow_is_rejected():
    registry = InMemoryEmailWorkflowRegistry()

    with pytest.raises(
        KeyError,
        match="Workflow not found",
    ):
        registry.update(make_workflow())


def test_registry_does_not_mutate_original_workflow():
    registry = InMemoryEmailWorkflowRegistry()

    workflow = make_workflow()
    registry.create(workflow)

    updated = workflow.with_lifecycle(
        EmailWorkflowLifecycle.PAUSED
    )

    registry.update(updated)

    assert workflow.lifecycle is EmailWorkflowLifecycle.ACTIVE
    assert registry.get(workflow.workflow_id) == updated
