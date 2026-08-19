"""
Tests for Voice Notification Acceptance API.

Validates:

HTTP Request
      |
      ↓
Accept Notification
      |
      ↓
VoiceCallAcceptanceService
      |
      ↓
Voice Session Response


Does NOT:
- Test LiveKit.
- Test providers.
- Test repositories directly.
"""

from fastapi.testclient import TestClient


from app.main import app



client = TestClient(
    app
)



def test_accept_existing_voice_notification():
    """
    Verify accepting an existing notification.

    Expected:
    - HTTP 200
    - voice_call_id returned
    - session_id returned
    - character identity preserved
    """


    #
    # Create voice call trigger first.
    #
    # This simulates:
    #
    # VoiceCall
    #      |
    #      ↓
    # Invitation
    #      |
    #      ↓
    # Notification
    #

    trigger_response = client.post(
        "/voice/trigger",
        json={
            "learner_id": "learner-001",
            "character_id": "yeti",
            "world_id": "french_world",
            "language_code": "fr",
            "channel": "inbox",
        },
    )


    assert trigger_response.status_code == 200


    trigger_body = (
        trigger_response.json()
    )


    notification_id = (
        trigger_body["notification_id"]
    )


    voice_call_id = (
        trigger_body["voice_call_id"]
    )


    #
    # Accept notification
    #

    response = client.post(
        f"/voice/notification/{notification_id}/accept"
    )


    print(
        response.json()
    )


    assert response.status_code == 200


    body = response.json()


    assert body["voice_call_id"] == (
        voice_call_id
    )


    assert body["learner_id"] == (
        "learner-001"
    )


    assert body["character_id"] == (
        "yeti"
    )


    assert body["session_id"]


    assert body["state"]



def test_accept_unknown_notification():

    """
    Unknown notification must return 404.
    """


    response = client.post(
        "/voice/notification/unknown/accept"
    )


    assert response.status_code == 404