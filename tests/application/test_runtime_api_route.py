"""
Runtime API route integration tests.

Validates:

HTTP
 |
 v
FastAPI API Route
 |
 v
ExternalRuntimeService
 |
 v
CapabilityGateway
 |
 v
Runtime Response

The test uses controlled fakes.

It does not call:
- Parallel API
- Gemini
- Google Cloud
- external providers
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import (
    create_app,
)

from backend.api import routes

from backend.services.external_runtime_service import (
    ExternalRuntimeService,
)


class FakeRuntimeGateway:
    """
    Controlled Runtime gateway for API testing.
    """

    async def execute(
        self,
        context,
    ) -> dict[str, object]:
        return {
            "request_id": "test-runtime-request",
            "capability": "live_intelligence",
            "status": "completed",
            "output": {
                "results": [
                    {
                        "title": "AI News Result",
                        "source": "fake-provider",
                    }
                ]
            },
        }


def create_test_runtime_service() -> ExternalRuntimeService:
    """
    Create ExternalRuntimeService using
    a controlled gateway.
    """

    return ExternalRuntimeService(
        gateway=FakeRuntimeGateway(),
    )


def test_runtime_execute_api_route():
    """
    Validate:

    POST /runtime/execute

        ->
    ExternalRuntimeService

        ->
    Runtime Result
    """

    original_factory = (
        routes.create_external_runtime_service
    )

    routes.create_external_runtime_service = (
        create_test_runtime_service
    )

    try:
        app = create_app()

        client = TestClient(
            app,
        )

        response = client.post(
            "/runtime/execute",
            json={
                "capability": (
                    "live_intelligence"
                ),
                "payload": {
                    "query": (
                        "latest AI news"
                    ),
                },
                "user_id": (
                    "runtime-api-test-user"
                ),
            },
        )

    finally:
        routes.create_external_runtime_service = (
            original_factory
        )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["status"]
        == "completed"
    )

    assert (
        body["capability"]
        == "live_intelligence"
    )

    assert (
        body["request_id"]
        == "test-runtime-request"
    )

    assert (
        body["output"]["results"][0]["source"]
        == "fake-provider"
    )


def test_runtime_execute_requires_capability():
    """
    Validate API transport validation.
    """

    app = create_app()

    client = TestClient(
        app,
    )

    response = client.post(
        "/runtime/execute",
        json={
            "payload": {},
        },
    )

    assert response.status_code == 422