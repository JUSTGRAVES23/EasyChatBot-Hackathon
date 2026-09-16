import pytest

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from governance.api.governance_timeline_api import router


@pytest.mark.asyncio
async def test_timeline_api():

    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.get(
            "/governance/timeline"
        )

    assert response.status_code == 200
    assert "events" in response.json()

