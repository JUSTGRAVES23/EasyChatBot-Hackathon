import pytest

from application.bootstrap import (
    bootstrap_application,
    get_external_runtime_service,
    reset_bootstrap,
)
from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityType,
)


@pytest.mark.asyncio
async def test_internal_documentation_executes_through_application_runtime():
    reset_bootstrap()
    bootstrap_application()

    service = get_external_runtime_service()

    request = CapabilityRequest(
        capability=CapabilityType.INTERNAL_DOCUMENTATION_SEARCH,
        request_id="wp16-e2e-001",
        payload={
            "query": "runtime capability",
            "max_results": 3,
        },
        metadata={
            "test": "wp16-e2e",
        },
        requested_by="wp16-test",
    )

    result = await service.execute(request)

    assert result.request_id == "wp16-e2e-001"
    assert (
        result.capability
        == CapabilityType.INTERNAL_DOCUMENTATION_SEARCH
    )
    assert result.status == CapabilityExecutionStatus.COMPLETED
    assert result.error is None

    assert isinstance(result.output, dict)
    assert result.output["result_count"] <= 3
    assert isinstance(result.output["results"], list)

    for item in result.output["results"]:
        assert item["source_id"]
        assert item["title"]
        assert item["content"]
        assert item["location"]
        assert item["relevance"] > 0

