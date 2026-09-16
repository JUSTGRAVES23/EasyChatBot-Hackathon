import pytest

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from governance.api.governance_change_api import router


@pytest.mark.asyncio
async def test_create_change_api():

    app = FastAPI()
    app.include_router(router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        response = await client.post(
            "/governance/changes",
            json={
                "component": "openai",
                "action": "PAUSE_PROVIDER",
                "reason": "Provider incident",
                "requested_by": "admin",
                "change_type": "PROVIDER",
                "risk": "CRITICAL",
                "approval_id": "APR-001",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["change_id"].startswith("CHG-")
    assert body["change_type"] == "PROVIDER"
    assert body["risk"] == "CRITICAL"
    assert body["status"] == "PENDING_APPROVAL"

