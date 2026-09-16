"""
Runtime application end-to-end tests.

Validates the complete application boundary:

HTTP
 |
 v
FastAPI
 |
 v
RuntimeApplicationService
 |
 v
ExternalRuntimeService
 |
 v
CapabilityGateway


Uses controlled dependencies only.

Does not call:

- Parallel Search
- Gemini
- Google Cloud
- external providers
"""

from __future__ import annotations


from fastapi.testclient import TestClient


from api.main import (
    create_app,
)

from runtime.external_runtime_container import (
    configure_external_runtime_service,
    reset_runtime_container,
)

from services.external_runtime_service import (
    ExternalRuntimeService,
)


class FakeGateway:
    """
    Controlled capability gateway.
    """

    async def execute(
        self,
        request,
    ):
        return {
            "request_id": "e2e-runtime-test",
            "capability": request.capability,
            "status": "completed",
            "output": {
                "source": "fake-gateway",
            },
        }


def test_runtime_http_flow():
    """
    Validate:

    POST /runtime/execute

        ->
    RuntimeApplicationService

        ->
    ExternalRuntimeService

        ->
    CapabilityGateway
    """

    service = ExternalRuntimeService(
        gateway=FakeGateway(),
    )

    configure_external_runtime_service(
        service,
    )

    app = create_app()

    client = TestClient(
        app,
    )

    response = client.post(
        "/runtime/execute",
        json={
            "capability": "live_intelligence",
            "payload": {
                "query": "AI news",
            },
            "user_id": "e2e-test-user",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["request_id"]
        == "e2e-runtime-test"
    )

    assert (
        body["status"]
        == "completed"
    )

    assert (
        body["output"]["source"]
        == "fake-gateway"
    )
