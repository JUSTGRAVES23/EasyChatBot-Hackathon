"""
EasyChatBot Operations Center HTTP bootstrap tests.

Validates that the existing FastAPI application bootstrap
registers the Operations Center router.

This test intentionally verifies the existing application
bootstrap boundary. It does not create a second FastAPI app
or a second Runtime.
"""

from fastapi.testclient import TestClient

from backend.api.main import create_app


def test_operations_center_dashboard_route_is_registered() -> None:
    """
    The existing FastAPI application must expose the
    Operations Center dashboard endpoint.
    """

    app = create_app()

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = client.get(
        "/api/operations-center/dashboard"
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(
        body,
        dict,
    )


def test_operations_center_operational_events_route_is_registered() -> None:
    """
    The existing FastAPI application must expose the
    read-only operational-events endpoint.
    """

    app = create_app()

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = client.get(
        "/api/operations-center/operational-events"
    )

    assert response.status_code == 200

    body = response.json()

    assert isinstance(
        body,
        list,
    )


def test_operations_center_routes_are_read_only() -> None:
    """
    Operations Center endpoints must remain GET-only.
    """

    app = create_app()

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    dashboard_response = client.post(
        "/api/operations-center/dashboard"
    )

    events_response = client.post(
        "/api/operations-center/operational-events"
    )

    assert dashboard_response.status_code == 405
    assert events_response.status_code == 405