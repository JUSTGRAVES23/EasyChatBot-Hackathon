"""
Tests for Voice Call Trigger API.

Validates HTTP boundary:

HTTP
 |
 ↓
Trigger Service
 |
 ↓
VoiceCall
 |
 ↓
Invitation
 |
 ↓
Notification
"""

from fastapi.testclient import TestClient


from app.main import app



client = TestClient(
    app
)



def test_trigger_voice_call():

    response = client.post(
        "/voice/trigger",
        json={
            "learner_id": "learner-001",
            "character_id": "yeti",
            "world_id": "french_world",
            "language_code": "fr",
            "channel": "inbox",
        },
    )


    print(
        response.json()
    )


    assert response.status_code == 200


    body = response.json()


    assert body["voice_call_id"]


    assert body["invitation_id"]


    assert body["notification_id"]



def test_trigger_voice_call_invalid_payload():

    response = client.post(
        "/voice/trigger",
        json={
            "learner_id": "",
        },
    )


    assert response.status_code in [
        400,
        422,
    ]