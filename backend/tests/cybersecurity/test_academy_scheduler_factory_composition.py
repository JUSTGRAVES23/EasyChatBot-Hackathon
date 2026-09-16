from unittest.mock import MagicMock

from cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)


def test_scheduler_factory_accepts_existing_academy_workflow():
    academy_workflow = MagicMock()

    runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=academy_workflow,
    )

    adapter = runtime.scheduler_adapter

    assert adapter.academy_one_week_workflow is academy_workflow


def test_scheduler_factory_creates_one_shared_scheduler():
    academy_workflow = MagicMock()

    runtime = create_cybersecurity_scheduler_runtime(
        workflow_service=MagicMock(),
        academy_one_week_workflow=academy_workflow,
    )

    adapter = runtime.scheduler_adapter

    assert adapter.scheduler is not None
    assert adapter.academy_one_week_workflow is academy_workflow
    assert adapter.scheduler.running is False
