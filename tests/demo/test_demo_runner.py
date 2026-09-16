import pytest

from demo.demo_runner import DemoRunner


@pytest.mark.asyncio
async def test_demo_runner():

    result = await DemoRunner().run(
        "cybersecurity",
        {
            "event": "CYBERSECURITY_ALERT",
            "component": "email_delivery",
        },
    )

    assert result.audit["status"] == "recorded"
    assert result.timeline["evidence_available"] is True

