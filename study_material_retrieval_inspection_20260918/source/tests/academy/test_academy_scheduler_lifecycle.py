from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cybersecurity.scheduler.cybersecurity_scheduler_runtime import (
    CybersecuritySchedulerRuntime,
)


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_shared_scheduler_lifecycle_starts_and_stops_cleanly():
    """
    The shared scheduler runtime must start and stop cleanly.

    Academy is already injected into the existing scheduler boundary.
    """

    adapter = MagicMock(
        name="scheduler_adapter",
    )

    adapter.start = MagicMock(
        name="start",
    )

    adapter.shutdown = MagicMock(
        name="shutdown",
    )

    runtime = CybersecuritySchedulerRuntime(
        scheduler_adapter=adapter,
    )

    await runtime.start()

    adapter.start.assert_called_once()

    await runtime.stop()

    adapter.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_lifecycle_does_not_execute_academy_workflow():
    """
    Starting/stopping the scheduler lifecycle must not directly execute
    the Academy workflow.
    """

    scheduler = MagicMock(
        name="shared_scheduler",
    )

    scheduler.running = False

    academy_workflow = MagicMock(
        name="academy_one_week_workflow",
    )

    adapter = MagicMock(
        name="scheduler_adapter",
    )

    adapter.scheduler = scheduler
    adapter.academy_one_week_workflow = academy_workflow

    adapter.start = MagicMock(
        name="start",
    )

    adapter.shutdown = MagicMock(
        name="shutdown",
    )

    runtime = CybersecuritySchedulerRuntime(
        scheduler_adapter=adapter,
    )

    await runtime.start()
    await runtime.stop()

    academy_workflow.run.assert_not_called()


def test_scheduler_runtime_uses_existing_adapter():
    """
    Runtime must use the supplied scheduler adapter rather than creating
    scheduler infrastructure itself.
    """

    adapter = MagicMock(
        name="existing_scheduler_adapter",
    )

    runtime = CybersecuritySchedulerRuntime(
        scheduler_adapter=adapter,
    )

    assert runtime.scheduler_adapter is adapter
