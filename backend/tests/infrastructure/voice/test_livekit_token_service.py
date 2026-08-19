"""
Tests for LiveKit Token Service.

Validates the infrastructure boundary
for creating provider-independent voice
connection credentials.
"""

from datetime import datetime


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)



def test_create_livekit_token():

    service = LiveKitTokenService()


    token = service.create_token(
        room_name="yeti-room-001",
    )


    assert isinstance(
        token,
        VoiceConnectionToken,
    )


    assert token.room_name == (
        "yeti-room-001"
    )


    assert token.provider == (
        "livekit"
    )


    assert token.token.startswith(
        "livekit-"
    )


    assert token.expires_at > (
        datetime.utcnow()
    )



def test_custom_expiration_time():

    service = LiveKitTokenService()


    token = service.create_token(
        room_name="room-001",
        expires_minutes=60,
    )


    assert token.expires_at > (
        datetime.utcnow()
    )



def test_empty_room_name_is_rejected():

    service = LiveKitTokenService()


    try:

        service.create_token(
            room_name="",
        )


        assert False


    except ValueError:

        assert True



def test_invalid_expiration_is_rejected():

    service = LiveKitTokenService()


    try:

        service.create_token(
            room_name="room-001",
            expires_minutes=0,
        )


        assert False


    except ValueError:

        assert True