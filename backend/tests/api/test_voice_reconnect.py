"""
Tests for Voice Reconnect API.

Validates:
- Existing voice call can reconnect.
- Same voice_call_id is preserved.
- Unknown calls are rejected.
"""

from fastapi.testclient import TestClient


from app.main import app


from app.application.composition.voice_call_management_composition import (
    build_voice_call_management_service,
)



client = TestClient(
    app
)



def create_voice_call():

    service = (
        build_voice_call_management_service()
    )


    voice_call = (
        service.create_call(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
        )
    )


    disconnected = (
        voice_call
        .mark_disconnected()
    )


    service.repository.save(
        voice_call=disconnected,
    )


    return voice_call



def test_reconnect_existing_voice_call():

    voice_call = (
        create_voice_call()
    )


    response = client.post(
        f"/voice/call/{voice_call.id}/reconnect"
    )


    print(
        response.json()
    )


    assert response.status_code == 200


    body = response.json()


    assert body["voice_call_id"] == (
        voice_call.id
    )


    assert body["character_id"] == (
        "yeti"
    )


    assert body["language_code"] == (
        "fr"
    )


    assert body["state"] == (
        "ready"
    )



def test_reconnect_unknown_voice_call():

    response = client.post(
        "/voice/call/unknown/reconnect"
    )


    assert response.status_code == 404