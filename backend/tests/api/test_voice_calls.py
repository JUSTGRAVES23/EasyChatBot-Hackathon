"""
Tests for Voice Calls API.

Validates the HTTP boundary
for preparing character voice calls.
"""

from fastapi.testclient import TestClient


from app.main import app



client = TestClient(
    app
)



def test_prepare_voice_call():

    response = client.post(
        "/voice/call",
        json={
            "learner_id": "learner-001",
            "world_id": "french_world",
            "character_id": "yeti",
            "language_code": "fr",
        },
    )


    print(
        "\nVOICE CALL STATUS:",
        response.status_code,
    )


    print(
        "VOICE CALL BODY:",
        response.json(),
    )


    assert response.status_code == 200


    body = response.json()


    assert body["character_id"] == (
        "yeti"
    )


    assert body["language_code"] == (
        "fr"
    )


    assert body["room_name"]


    assert body["provider"] == (
        "livekit"
    )


    assert body["state"] == (
        "active"
    )


    assert "token" in body


    # Real LiveKit access tokens are
    # signed JWT credentials.
    assert body["token"]


    assert body["token"].count(".") == 2


    assert body["token"].startswith(
        "eyJ"
    )


    assert "expires_at" in body


    assert body["expires_at"]



def test_prepare_voice_call_invalid_payload():

    response = client.post(
        "/voice/call",
        json={
            "learner_id": "",
            "world_id": "unknown_world",
            "character_id": "unknown",
            "language_code": "fr",
        },
    )


    assert response.status_code in [
        400,
        422,
    ]