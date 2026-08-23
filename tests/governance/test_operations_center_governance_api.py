
import pytest

from fastapi import FastAPI

from httpx import (
    ASGITransport,
    AsyncClient,
)

from backend.governance.api.governance_operations_api import (
    router,
    get_dashboard_service,
)

from backend.governance.operations_center.governance_dashboard_service import (
    GovernanceDashboardService,
)


class FakeControl:

    def __init__(self):
        self.paused = True

    def is_paused(self):
        return self.paused

    def status(self):
        return {
            "paused": True,
            "reason": "Security incident",
            "changed_at": "2026-08-21T10:00:00Z",
        }


@pytest.mark.asyncio
async def test_operations_center_returns_governance_state():

    service = GovernanceDashboardService(
        provider_control=FakeControl()
    )

    app = FastAPI()

    app.include_router(router)

    app.dependency_overrides[
        get_dashboard_service
    ] = lambda: service


    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/operations/governance/status"
        )


    assert response.status_code == 200

    body = response.json()

    assert (
        body["controls"][0]["status"]
        == "paused"
    )

    assert (
        "Security incident"
        in body["yeti"]["message"]
    )
