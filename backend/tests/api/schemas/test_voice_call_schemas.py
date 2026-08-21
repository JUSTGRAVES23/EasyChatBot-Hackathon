"""
Tests for Voice Call API Schemas.

Validates:

- Request schema creation.
- Response schema creation.
- Serialization behaviour.
- Stable frontend API contracts.

Does NOT:
- Test business logic.
- Test services.
- Test persistence.
"""



from app.api.schemas.voice_call import (
    VoiceCallTriggerRequestSchema,
    VoiceCallTriggerResponseSchema,
    VoiceCallAcceptanceResponseSchema,
    VoiceReconnectResponseSchema,
)



def test_voice_call_trigger_request_schema():

    schema = (
        VoiceCallTriggerRequestSchema(
            learner_id="learner-001",
            character_id="yeti",
            world_id="french_world",
            language_code="fr",
            channel="inbox",
        )
    )


    assert schema.learner_id == (
        "learner-001"
    )


    assert schema.character_id == (
        "yeti"
    )


    assert schema.world_id == (
        "french_world"
    )


    assert schema.language_code == (
        "fr"
    )


    assert schema.channel == (
        "inbox"
    )



def test_voice_call_trigger_response_schema():

    schema = (
        VoiceCallTriggerResponseSchema(
            voice_call_id="vc-001",
            invitation_id="inv-001",
            notification_id="notification-001",
        )
    )


    payload = (
        schema.model_dump()
    )


    assert payload[
        "voice_call_id"
    ] == "vc-001"


    assert payload[
        "invitation_id"
    ] == "inv-001"


    assert payload[
        "notification_id"
    ] == "notification-001"



def test_voice_call_acceptance_response_schema():

    schema = (
        VoiceCallAcceptanceResponseSchema(
            voice_call_id="vc-001",
            learner_id="learner-001",
            character_id="yeti",
            session_id="vc-001-session",
            state="ready",
        )
    )


    assert schema.voice_call_id == (
        "vc-001"
    )


    assert schema.learner_id == (
        "learner-001"
    )


    assert schema.character_id == (
        "yeti"
    )


    assert schema.session_id == (
        "vc-001-session"
    )


    assert schema.state == (
        "ready"
    )



def test_voice_reconnect_response_schema():

    schema = (
        VoiceReconnectResponseSchema(
            voice_call_id="vc-001",
            session_id="vc-001-reconnect",
            state="active",
        )
    )


    payload = (
        schema.model_dump()
    )


    assert payload[
        "voice_call_id"
    ] == "vc-001"


    assert payload[
        "session_id"
    ] == "vc-001-reconnect"


    assert payload[
        "state"
    ] == "active"



def test_schema_serialization():

    schema = (
        VoiceCallTriggerResponseSchema(
            voice_call_id="vc-001",
            invitation_id="inv-001",
            notification_id="notification-001",
        )
    )


    json_payload = (
        schema.model_dump_json()
    )


    assert "vc-001" in (
        json_payload
    )


    assert "inv-001" in (
        json_payload
    )


    assert "notification-001" in (
        json_payload
    )