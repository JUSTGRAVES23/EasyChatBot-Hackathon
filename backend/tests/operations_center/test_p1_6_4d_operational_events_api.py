from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.operations_center import (
    create_operations_center_router,
)
from app.application.health.operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSeverity,
    OperationalSurface,
)
from app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition,
)


def make_client() -> tuple[TestClient, OperationsCenterComposition]:
    composition = OperationsCenterComposition()

    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(
        create_operations_center_router(
            composition=composition,
        )
    )

    return TestClient(app), composition


def test_operational_events_endpoint_returns_empty_list_when_no_events():
    client, _composition = make_client()

    response = client.get(
        "/api/operations-center/operational-events"
    )

    assert response.status_code == 200
    assert response.json() == []


def test_operational_events_endpoint_serializes_recorded_events():
    client, composition = make_client()

    composition.event_service.record_event(
        OperationalEvent(
            event_type=OperationalEventType.MESSAGE_FAILURE,
            surface=OperationalSurface.PRIVATE_CLASSROOM,
            correlation_id="api-test-001",
            severity=OperationalSeverity.HIGH,
            metadata={
                "safe_status": "timeout",
            },
        )
    )

    response = client.get(
        "/api/operations-center/operational-events"
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["event_type"] == "message_failure"
    assert payload[0]["surface"] == "private_classroom"
    assert payload[0]["correlation_id"] == "api-test-001"
    assert payload[0]["severity"] == "high"
    assert payload[0]["metadata"]["safe_status"] == "timeout"


def test_operational_events_endpoint_flattens_correlated_events():
    client, composition = make_client()

    for correlation_id in (
        "api-test-002",
        "api-test-003",
    ):
        composition.event_service.record_event(
            OperationalEvent(
                event_type=OperationalEventType.MESSAGE_FAILURE,
                surface=OperationalSurface.PRIVATE_CLASSROOM,
                correlation_id=correlation_id,
            )
        )

    response = client.get(
        "/api/operations-center/operational-events"
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 2

    correlation_ids = {
        event["correlation_id"]
        for event in payload
    }

    assert correlation_ids == {
        "api-test-002",
        "api-test-003",
    }

