"""EasyChatBot AI Operations Center HTTP router tests.

Validates the dashboard and operational-events HTTP boundaries.

The tests isolate all application dependencies and never call
external provider services.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient


from app.application.provider_management.operations_center_dashboard_api import (
    OperationsCenterDashboardAPI,
)

from app.application.provider_management.operations_center_operational_events_api import (
    OperationsCenterOperationalEventsAPI,
)

from app.interfaces.provider_management.operations_center_dashboard_router import (
    get_dashboard_api,
    get_health_refresh_service,
    get_operational_events_api,
    router,
)



def create_test_dashboard_api() -> OperationsCenterDashboardAPI:
    """
    Create deterministic dashboard API test double.
    """

    class TestDashboardAPI:

        def get_dashboard(self) -> dict:
            return {
                "system_confidence": 92.0,
                "monitoring_status": "healthy",
                "active_providers": [
                    {
                        "provider": "openai",
                        "model": "gpt-5-mini",
                        "capabilities": [
                            "conversation",
                            "reasoning",
                        ],
                        "active": True,
                    },
                    {
                        "provider": "gemini",
                        "model": "gemini-2.5-flash",
                        "capabilities": [
                            "summarisation",
                        ],
                        "active": True,
                    },
                ],
                "provider_intelligence": [],
                "active_escalations": 0,
                "pending_approvals": 0,
                "approved_escalations": 0,
                "rejected_escalations": 0,
                "pending_notifications": 0,
                "total_escalations": 0,
            }

    return TestDashboardAPI()  # type: ignore[return-value]



def create_test_operational_events_api() -> (
    OperationsCenterOperationalEventsAPI
):
    """
    Create deterministic operational-events API test double.
    """

    class TestOperationalEventsAPI:

        def list_events(self) -> list[dict]:
            return [
                {
                    "event_id": (
                        "00000000-0000-0000-0000-000000000001"
                    ),
                    "event_type": (
                        "provider_incident_created"
                    ),
                    "severity": "critical",
                    "source": "provider_management",
                    "component": (
                        "ProviderIncidentService"
                    ),
                    "occurred_at": (
                        "2026-08-15T14:00:00+00:00"
                    ),
                    "message": (
                        "Provider incident created."
                    ),
                    "correlation_id": "incident-001",
                    "metadata": {
                        "provider": "openai",
                    },
                }
            ]

    return TestOperationalEventsAPI()  # type: ignore[return-value]



def create_test_health_refresh_service():
    """
    Create deterministic no-op health refresh service.

    Tests must never depend on provider credentials or
    external provider availability.
    """

    class TestHealthRefreshService:

        async def refresh(self) -> None:
            return None

    return TestHealthRefreshService()



def create_test_app() -> FastAPI:
    """
    Create a minimal FastAPI application with the router.
    """

    app = FastAPI(
        title="EasyChatBot AI Operations Center"
    )

    app.include_router(router)


    app.dependency_overrides[
        get_dashboard_api
    ] = (
        create_test_dashboard_api
    )


    app.dependency_overrides[
        get_operational_events_api
    ] = (
        create_test_operational_events_api
    )


    app.dependency_overrides[
        get_health_refresh_service
    ] = (
        create_test_health_refresh_service
    )


    return app



def test_dashboard_endpoint_returns_success() -> None:

    app = create_test_app()

    response = TestClient(app).get(
        "/api/operations-center/dashboard"
    )

    assert response.status_code == 200



def test_dashboard_endpoint_returns_json() -> None:

    app = create_test_app()

    response = TestClient(app).get(
        "/api/operations-center/dashboard"
    )

    assert response.headers[
        "content-type"
    ].startswith(
        "application/json"
    )

    assert isinstance(
        response.json(),
        dict,
    )



def test_dashboard_endpoint_exposes_expected_contract() -> None:

    app = create_test_app()

    body = TestClient(app).get(
        "/api/operations-center/dashboard"
    ).json()


    assert body["system_confidence"] == 92.0

    assert body["monitoring_status"] == "healthy"

    assert body["active_escalations"] == 0

    assert body["pending_approvals"] == 0

    assert body["approved_escalations"] == 0

    assert body["rejected_escalations"] == 0

    assert body["pending_notifications"] == 0

    assert body["total_escalations"] == 0



def test_dashboard_endpoint_exposes_provider_data() -> None:

    app = create_test_app()

    body = TestClient(app).get(
        "/api/operations-center/dashboard"
    ).json()


    providers = body[
        "active_providers"
    ]


    assert len(providers) == 2

    assert providers[0]["provider"] == "openai"

    assert providers[0]["model"] == "gpt-5-mini"

    assert providers[0]["active"] is True

    assert providers[1]["provider"] == "gemini"



def test_dashboard_endpoint_is_read_only() -> None:

    app = create_test_app()

    response = TestClient(app).post(
        "/api/operations-center/dashboard"
    )

    assert response.status_code == 405



def test_operational_events_endpoint_returns_success() -> None:

    app = create_test_app()

    response = TestClient(app).get(
        "/api/operations-center/operational-events"
    )

    assert response.status_code == 200



def test_operational_events_endpoint_returns_json() -> None:

    app = create_test_app()

    response = TestClient(app).get(
        "/api/operations-center/operational-events"
    )


    assert response.headers[
        "content-type"
    ].startswith(
        "application/json"
    )


    assert isinstance(
        response.json(),
        list,
    )



def test_operational_events_endpoint_exposes_event_contract() -> None:

    app = create_test_app()

    body = TestClient(app).get(
        "/api/operations-center/operational-events"
    ).json()


    assert len(body) == 1


    event = body[0]


    assert event["event_type"] == (
        "provider_incident_created"
    )

    assert event["severity"] == "critical"

    assert event["source"] == (
        "provider_management"
    )

    assert event["component"] == (
        "ProviderIncidentService"
    )

    assert event["correlation_id"] == (
        "incident-001"
    )

    assert event["metadata"]["provider"] == (
        "openai"
    )



def test_operational_events_endpoint_is_read_only() -> None:

    app = create_test_app()

    response = TestClient(app).post(
        "/api/operations-center/operational-events"
    )

    assert response.status_code == 405



def test_production_operational_events_dependency_is_configured() -> None:

    app = FastAPI(
        title="EasyChatBot AI Operations Center"
    )

    app.include_router(router)


    client = TestClient(
        app,
        raise_server_exceptions=False,
    )


    response = client.get(
        "/api/operations-center/operational-events"
    )


    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )

    assert response.json() == []