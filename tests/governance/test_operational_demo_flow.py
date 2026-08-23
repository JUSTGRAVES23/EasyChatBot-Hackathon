import pytest


@pytest.mark.asyncio
async def test_operational_demo_flow():

    event = {
        "event": "PROVIDER_PAUSED",
        "component": "AI_PROVIDER",
    }

    assert event["event"] == "PROVIDER_PAUSED"
    assert event["component"] == "AI_PROVIDER"
