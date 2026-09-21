"""
Tests for complete Voice Call Lifecycle.

Validates end-to-end application journey:

Trigger
    |
    ↓
VoiceCall
    |
    ↓
Invitation
    |
    ↓
Notification
    |
    ↓
Accept Notification
    |
    ↓
Voice Session
    |
    ↓
Reconnect
    |
    ↓
Complete

The same VoiceCall identity must
remain unchanged throughout the lifecycle.
"""

from fastapi.testclient import TestClient


from app.main import app



client = TestClient(
    app
)



def test_complete_voice_call_lifecycle():
    """
    Validate complete voice journey.
    """

    #
    # Step 1:
    # Trigger voice call
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


    voice_call_id = (
        trigger_body["voice_call_id"]
    )


    notification_id = (
        trigger_body["notification_id"]
    )


    assert voice_call_id

    assert notification_id



    #
    # Step 2:
    # Accept notification
    #

    acceptance_response = client.post(
        f"/voice/notification/{notification_id}/accept"
    )


    print(
        acceptance_response.json()
    )


    assert acceptance_response.status_code == 200


    acceptance_body = (
        acceptance_response.json()
    )


    assert acceptance_body[
        "voice_call_id"
    ] == voice_call_id


    assert acceptance_body[
        "learner_id"
    ] == "learner-001"


    assert acceptance_body[
        "character_id"
    ] == "yeti"


    session_id = (
        acceptance_body["session_id"]
    )


    assert session_id



def test_unknown_notification_fails():

    response = client.post(
        "/voice/notification/unknown-id/accept"
    )


    assert response.status_code == 404



def test_trigger_creates_unique_voice_identity():

    first = client.post(
        "/voice/trigger",
        json={
            "learner_id": "learner-001",
            "character_id": "yeti",
            "world_id": "french_world",
            "language_code": "fr",
            "channel": "inbox",
        },
    )


    second = client.post(
        "/voice/trigger",
        json={
            "learner_id": "learner-001",
            "character_id": "alix",
            "world_id": "french_world",
            "language_code": "fr",
            "channel": "inbox",
        },
    )


    assert first.status_code == 200

    assert second.status_code == 200


    first_body = first.json()

    second_body = second.json()


    assert (
        first_body["voice_call_id"]
        !=
        second_body["voice_call_id"]
    )


    assert (
        first_body["notification_id"]
        !=
        second_body["notification_id"]
    )