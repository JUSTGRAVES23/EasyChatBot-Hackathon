"""
Tests for the Podcast Discovery API endpoint.

The API endpoint must remain a thin transport boundary.

Architecture:

HTTP
 |
 v
API Schema
 |
 v
ExternalRuntimeService
 |
 v
CapabilityGateway
 |
 v
PodcastDiscoveryExecutor
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient

from backend.api.main import app

from src.ai_runtime.capabilities.models import (
    CapabilityExecutionStatus,
    CapabilityResult,
    CapabilityType,
)


client = TestClient(app)


def test_podcast_discovery_endpoint_exists():
    """
    Verify that the Podcast Discovery endpoint exists.
    """

    response = client.post(
        "/capabilities/podcast/discover",
        json={
            "query": "French learning podcast",
            "target_language": "fr",
            "learner_level": "B2",
        },
    )

    assert response.status_code != 404


def test_podcast_discovery_endpoint_delegates_to_runtime_service():
    """
    Verify that the endpoint delegates execution to the
    ExternalRuntimeService boundary.
    """

    expected_result = CapabilityResult(
        request_id="podcast-api-test-001",
        capability=CapabilityType.PODCAST_DISCOVERY,
        status=CapabilityExecutionStatus.COMPLETED,
        output={
            "podcast": "French Podcast",
        },
    )

    service = Mock()

    service.execute = AsyncMock(
        return_value=expected_result,
    )

    with patch(
        "backend.api.routes.create_external_runtime_service",
        return_value=service,
    ):
        response = client.post(
            "/capabilities/podcast/discover",
            json={
                "query": "French learning podcast",
                "target_language": "fr",
                "learner_level": "B2",
            },
        )

    assert response.status_code == 200

    service.execute.assert_awaited_once()


def test_podcast_discovery_endpoint_rejects_missing_query():
    """
    Verify that missing query input is rejected.
    """

    response = client.post(
        "/capabilities/podcast/discover",
        json={
            "target_language": "fr",
            "learner_level": "B2",
        },
    )

    assert response.status_code in (
        400,
        422,
    )