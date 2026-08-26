from __future__ import annotations

import pytest

from backend.app.application.health.operational_event import (
    OperationalEvent,
    OperationalEventType,
    OperationalSurface,
)
from backend.app.application.operations_center.dashboard_composition import (
    OperationsCenterComposition,
)
from backend.app.application.operations_center.dashboard_facade import (
    OperationsCenterDashboardFacade,
)


@pytest.mark.asyncio
async def test_ws21_14_composition_exposes_real_dashboard_contract():
    composition = OperationsCenterComposition()

    payload = await composition.dashboard_api.get_dashboard()

    assert "generated_at" in payload
    assert "overall" in payload
    assert "private_classroom" in payload
    assert "announcement_group" in payload
    assert "incidents" in payload

    assert "status" in payload["overall"]
    assert "health_score" in payload["overall"]


@pytest.mark.asyncio
async def test_ws21_14_event_service_is_persistent_within_composition():
    composition = OperationsCenterComposition()

    event = OperationalEvent(
        event_type=OperationalEventType.MESSAGE_FAILURE,
        surface=OperationalSurface.PRIVATE_CLASSROOM,
        correlation_id="ws21-14-test",
    )

    composition.event_service.record_event(event)

    first = await composition.dashboard_api.get_dashboard()
    second = await composition.dashboard_api.get_dashboard()

    assert any(
        incident["correlation_id"] == "ws21-14-test"
        for incident in first["incidents"]
    )
    assert any(
        incident["correlation_id"] == "ws21-14-test"
        for incident in second["incidents"]
    )


def test_ws21_14_facade_requires_real_dashboard_service():
    with pytest.raises(ValueError):
        OperationsCenterDashboardFacade(dashboard_service=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_ws21_14_dashboard_contract_contains_no_learner_content():
    composition = OperationsCenterComposition()

    event = OperationalEvent(
        event_type=OperationalEventType.MESSAGE_FAILURE,
        surface=OperationalSurface.PRIVATE_CLASSROOM,
        correlation_id="ws21-14-safe",
        metadata={
            "reason": "message_processing_failed",
        },
    )
    composition.event_service.record_event(event)

    payload = await composition.dashboard_api.get_dashboard()
    text = str(payload).lower()

    assert "prompt" not in text
    assert "response" not in text
    assert "password" not in text
    assert "secret" not in text
    assert "api_key" not in text
    assert "bot_token" not in text
    assert "database_url" not in text
