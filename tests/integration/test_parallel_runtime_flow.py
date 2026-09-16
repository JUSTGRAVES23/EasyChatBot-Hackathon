"""
Parallel Runtime vertical slice integration test.

Validates:

Application Bootstrap
|
v
ExternalRuntimeService
|
v
CapabilityGateway
|
v
PodcastDiscoveryExecutor
|
v
ParallelPodcastProvider

No external services are called.
"""

from __future__ import annotations


import pytest


from application.bootstrap import (
    bootstrap_application,
    reset_bootstrap,
)


from runtime.external_runtime_container import (
    get_external_runtime_service,
    reset_runtime_container,
)


from src.ai_runtime.capabilities.models import (
    CapabilityRequest,
    CapabilityType,
)


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """
    Keep integration tests isolated.
    """

    reset_bootstrap()
    reset_runtime_container()

    yield

    reset_bootstrap()
    reset_runtime_container()


@pytest.mark.asyncio
async def test_parallel_runtime_vertical_flow():
    """
    Validate:

    Bootstrap
        ->
    Runtime Service
        ->
    Capability Execution
        ->
    Provider Boundary
    """

    bootstrap_application()

    runtime_service = (
        get_external_runtime_service()
    )

    request = CapabilityRequest(
        request_id=(
            "parallel-test-request"
        ),
        capability=(
            CapabilityType.PODCAST_DISCOVERY
        ),
        payload={
            "user_id": (
                "parallel-test-user"
            ),
            "query": (
                "French learning podcast"
            ),
            "target_language": (
                "fr"
            ),
            "learner_level": (
                "B2"
            ),

            # Character context required by
            # PodcastRecommendationService
            "character_id": (
                "julie"
            ),
            "character_name": (
                "Julie"
            ),
            "character_message": (
                "I found this podcast to help "
                "you practise French listening."
            ),
        },
    )

    result = await runtime_service.execute(
        request,
    )

    assert result is not None

    assert (
        result.request_id
        == "parallel-test-request"
    )

    assert (
        result.capability
        == CapabilityType.PODCAST_DISCOVERY
    )

    assert result.status.value == "completed"
