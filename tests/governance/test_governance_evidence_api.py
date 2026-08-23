import pytest

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from backend.governance.api.governance_evidence_api import (
    router,
    get_evidence_service,
)


class FakeService:

    def timeline(self):
        return [
            {
                "event": "PROVIDER_PAUSED"
            }
        ]


@pytest.mark.asyncio
async def test_governance_timeline_endpoint():

    app = FastAPI()

    app.include_router(router)

    app.dependency_overrides[
        get_evidence_service
    ] = lambda: FakeService()


    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/operations/governance/timeline"
        )


    assert response.status_code == 200
    assert response.json()["events"][0]["event"] == "PROVIDER_PAUSED"
