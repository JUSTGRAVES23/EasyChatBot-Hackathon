"""
Tests for the External Runtime application service.

The production service does not exist yet.

These tests define the required application-layer contract before
implementation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from src.ai_runtime.capabilities.gateway import (
    CapabilityGateway,
)

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityRequest,
    CapabilityResult,
    CapabilityType,
)

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)


def make_request() -> CapabilityRequest:
    """
    Create a minimal external Runtime capability request.
    """

    return CapabilityRequest(
        capability=CapabilityType.PODCAST_DISCOVERY,
        request_id="application-runtime-test-001",
        payload={
            "query": "French learning podcast",
        },
        requested_by="learning_application",
    )


@pytest.mark.asyncio
async def test_external_runtime_service_delegates_to_gateway():
    """
    Verify that the application service delegates execution to
    the injected CapabilityGateway.
    """

    gateway = Mock(
        spec=CapabilityGateway,
    )

    expected_result = CapabilityResult(
        request_id="application-runtime-test-001",
        capability=CapabilityType.PODCAST_DISCOVERY,
        status=CapabilityExecutionStatus.COMPLETED,
        output={
            "ok": True,
        },
    )

    gateway.execute = AsyncMock(
        return_value=expected_result,
    )

    service = ExternalRuntimeService(
        gateway=gateway,
    )

    request = make_request()

    result = await service.execute(
        request,
    )

    assert result is expected_result

    gateway.execute.assert_awaited_once_with(
        request,
    )


def test_external_runtime_service_requires_gateway():
    """
    Verify that the application service rejects a missing gateway.
    """

    with pytest.raises(
        ValueError,
        match="CapabilityGateway cannot be None",
    ):
        ExternalRuntimeService(
            gateway=None,  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_external_runtime_service_rejects_missing_request():
    """
    Verify that the application service rejects a missing request
    before attempting Runtime execution.
    """

    gateway = Mock(
        spec=CapabilityGateway,
    )

    gateway.execute = AsyncMock()

    service = ExternalRuntimeService(
        gateway=gateway,
    )

    with pytest.raises(
        ValueError,
        match="CapabilityRequest cannot be None",
    ):
        await service.execute(
            None,  # type: ignore[arg-type]
        )

    gateway.execute.assert_not_awaited()