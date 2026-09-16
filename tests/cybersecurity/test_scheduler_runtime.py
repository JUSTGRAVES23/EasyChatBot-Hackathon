"""
Tests for Cybersecurity Scheduler Runtime.

Validates:
- scheduler starts;
- jobs register;
- scheduler stops.

Does NOT test:
- FastAPI;
- routers;
- APIs;
- email providers.
"""


import pytest


from cybersecurity.scheduler.cybersecurity_scheduler_runtime import (
    CybersecuritySchedulerRuntime,
)


from cybersecurity.scheduler.cybersecurity_job_registry import (
    CybersecurityJobRegistry,
)



@pytest.mark.asyncio
async def test_scheduler_runtime_start_registers_jobs():

    registry = (
        CybersecurityJobRegistry()
    )


    runtime = (
        CybersecuritySchedulerRuntime(
            job_registry=registry,
        )
    )


    await runtime.start()


    status = (
        runtime.status()
    )


    assert (
        status["started"]
        is True
    )


    assert (
        len(status["jobs"])
        == 3
    )



@pytest.mark.asyncio
async def test_scheduler_runtime_shutdown():

    registry = (
        CybersecurityJobRegistry()
    )


    runtime = (
        CybersecuritySchedulerRuntime(
            job_registry=registry,
        )
    )


    await runtime.start()


    await runtime.stop()


    status = (
        runtime.status()
    )


    assert (
        status["started"]
        is False
    )

