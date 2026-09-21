from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.operations_center.email_workflows.domain import (
    EmailWorkflowDefinition,
    EmailWorkflowLifecycle,
    EmailWorkflowType,
)
from app.infrastructure.persistence.database import Base
from app.infrastructure.persistence.email_workflow_models import (
    EmailWorkflowRecord,
)
from app.infrastructure.persistence.postgresql_email_workflow_registry import (
    PostgreSQLEmailWorkflowRegistry,
)


def make_workflow(
    workflow_id: str = "workflow.test",
    lifecycle: EmailWorkflowLifecycle = EmailWorkflowLifecycle.ACTIVE,
):
    now = datetime.now(timezone.utc)

    return EmailWorkflowDefinition(
        workflow_id=workflow_id,
        name="Test Workflow",
        description="PostgreSQL registry test",
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


def make_registry():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(
        engine,
        tables=[EmailWorkflowRecord.__table__],
    )

    return PostgreSQLEmailWorkflowRegistry(
        sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )
    )


def assert_same_instant(
    actual: datetime,
    expected: datetime,
) -> None:
    """Compare persisted timestamps by instant, independent of SQLite tz metadata."""
    actual_utc = (
        actual.replace(tzinfo=timezone.utc)
        if actual.tzinfo is None
        else actual.astimezone(timezone.utc)
    )

    expected_utc = (
        expected.replace(tzinfo=timezone.utc)
        if expected.tzinfo is None
        else expected.astimezone(timezone.utc)
    )

    assert actual_utc == expected_utc


def test_create_and_get():
    registry = make_registry()
    workflow = make_workflow()

    registry.create(workflow)

    result = registry.get(workflow.workflow_id)

    assert result is not None
    assert result.workflow_id == workflow.workflow_id
    assert result.name == workflow.name
    assert result.description == workflow.description
    assert result.workflow_type is workflow.workflow_type
    assert result.lifecycle is workflow.lifecycle
    assert result.owner == workflow.owner
    assert result.trigger == workflow.trigger
    assert result.schedule == workflow.schedule
    assert result.template_id == workflow.template_id
    assert result.version == workflow.version

    assert_same_instant(
        result.created_at,
        workflow.created_at,
    )
    assert_same_instant(
        result.updated_at,
        workflow.updated_at,
    )


def test_missing_workflow_returns_none():
    registry = make_registry()

    assert registry.get("missing.workflow") is None


def test_duplicate_workflow_is_rejected():
    registry = make_registry()
    workflow = make_workflow()

    registry.create(workflow)

    try:
        registry.create(workflow)
    except ValueError as exc:
        assert "Workflow already exists" in str(exc)
    else:
        raise AssertionError("Expected duplicate workflow rejection")


def test_list_returns_persisted_workflows():
    registry = make_registry()

    registry.create(make_workflow("workflow.b"))
    registry.create(make_workflow("workflow.a"))

    result = registry.list()

    assert [workflow.workflow_id for workflow in result] == [
        "workflow.a",
        "workflow.b",
    ]


def test_update_persists_lifecycle_and_version():
    registry = make_registry()
    workflow = make_workflow()

    registry.create(workflow)

    updated = workflow.with_lifecycle(
        EmailWorkflowLifecycle.PAUSED,
    )

    registry.update(updated)

    result = registry.get(workflow.workflow_id)

    assert result is not None
    assert result.lifecycle is EmailWorkflowLifecycle.PAUSED
    assert result.version == 2


def test_update_missing_workflow_is_rejected():
    registry = make_registry()

    try:
        registry.update(make_workflow())
    except KeyError as exc:
        assert "Workflow not found" in str(exc)
    else:
        raise AssertionError("Expected missing workflow rejection")