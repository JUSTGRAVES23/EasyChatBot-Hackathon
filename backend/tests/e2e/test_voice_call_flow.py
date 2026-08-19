"""
End-to-end test for voice call preparation flow.
"""

from fastapi.testclient import TestClient

from app.main import (
    app,
)


client = TestClient(
    app
)


def test_voice_call_preparation_flow():

    response = client.post(
        "/voice/call",
        json={
            "learner_id": "learner-001",
            "world_id": "french_world",
            "character_id": "yeti",
            "language_code": "fr",
        },
    )


    assert response.status_code == 200


    data = response.json()


    assert data["provider"] == (
        "livekit"
    )


    assert data["character_id"] == (
        "yeti"
    )


    assert data["language_code"] == (
        "fr"
    )


    assert data["room_name"].startswith(
        "yeti-"
    )