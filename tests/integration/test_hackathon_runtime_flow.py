"""
Hackathon Vertical Slice Runtime Integration Test.

WS-2 Sprint H2

Validates the application boundary only.

This test does not test:

- Runtime capability implementation
- Providers
- Agents

Those belong to other workstreams.

It validates:

API/Application boundary
        |
        v
Runtime Application Service
        |
        v
External Runtime Service
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock
from unittest.mock import Mock

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)

from backend.services.runtime.runtime_application_service import (
    RuntimeApplicationService,
)


@pytest.mark.asyncio
async def test_hackathon_vertical_slice_application_flow():
    """
    Validate the application runtime flow.

    Expected:

        User request
            |
            v
        RuntimeApplicationService
            |
            v
        ExternalRuntimeService
            |
            v
        Capability Result
    """

    expected_result = {
        "request_id": "hackathon-test-001",
        "capability": "live_intelligence",
        "status": "completed",
        "output": {
            "lesson": (
                "French lesson generated"
            )
        },
    }

    runtime_service = Mock()

    runtime_service.execute = AsyncMock(
        return_value=expected_result,
    )

    application_service = (
        RuntimeApplicationService(
            runtime_service=runtime_service,
        )
    )

    result = await application_service.execute(
        capability="live_intelligence",
        payload={
            "query": (
                "Teach French using today's AI news"
            )
        },
    )

    assert result == expected_result

    runtime_service.execute.assert_called_once()