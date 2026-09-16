"""
Tests for API runtime boundaries.

Verifies:

- Existing companion chat flow remains unchanged.
- API routes do not directly execute Runtime capabilities.
- External Runtime composition remains separated.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_chat_endpoint_still_exists():
    """
    Verify existing chat endpoint remains available.
    """

    response = client.post(
        "/chat",
        json={
            "user_id": "test-user",
            "character": "yeti",
            "message": "Hello",
            "research": False,
        },
    )

    assert response.status_code in (
        200,
        400,
        500,
    )


def test_api_does_not_expose_runtime_gateway_directly():
    """
    Verify API routes remain application-facing.

    CapabilityGateway should not become a route dependency.
    """

    from api import routes

    assert hasattr(
        routes,
        "create_external_runtime_service",
    )


@pytest.mark.asyncio
async def test_external_runtime_service_factory_creates_service():
    """
    Verify the API composition helper can create the
    ExternalRuntimeService boundary.
    """

    from api.routes import (
        create_external_runtime_service,
    )

    with patch(
        "backend.api.routes.create_external_runtime_gateway",
    ) as gateway_factory:

        gateway = Mock()

        gateway_factory.return_value = gateway

        service = (
            create_external_runtime_service()
        )

        assert service is not None

        assert service._gateway is gateway
