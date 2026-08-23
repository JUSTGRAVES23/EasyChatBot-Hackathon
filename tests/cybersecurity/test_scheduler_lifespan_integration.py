"""
Scheduler lifecycle integration tests.

Validates:

FastAPI lifecycle dependency
        |
        v
Scheduler Runtime

Does NOT test:
- cybersecurity intelligence;
- emails;
- APIs.
"""


import pytest


from backend.cybersecurity.scheduler.cybersecurity_scheduler_factory import (
    create_cybersecurity_scheduler_runtime,
)



@pytest.mark.asyncio
async def test_scheduler_factory_creates_runtime():


    runtime = (
        create_cybersecurity_scheduler_runtime()
    )


    assert runtime is not None



    await runtime.start()



    status = (
        runtime.status()
    )


    assert (
        status["started"]
        is True
    )



    await runtime.stop()



    status = (
        runtime.status()
    )


    assert (
        status["started"]
        is False
    )
