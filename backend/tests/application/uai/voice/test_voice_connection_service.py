"""
Tests for Voice Connection Service.

Validates the application boundary
for creating voice connection credentials.
"""

from app.application.uai.voice.voice_connection_service import (
    VoiceConnectionService,
)


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)



def create_service() -> VoiceConnectionService:
    """
    Create application service.
    """

    return VoiceConnectionService(
        token_service=(
            LiveKitTokenService()
        ),
    )



def test_create_connection_token():

    service = create_service()


    token = service.create_connection(
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


    # Real LiveKit access tokens
    # are signed JWT credentials.
    assert token.token


    assert token.token.count(".") == 2


    assert token.token.startswith(
        "eyJ"
    )



def test_connection_token_has_expiration():

    service = create_service()


    token = service.create_connection(
        room_name="room-001",
    )


    assert token.expires_at is not None



def test_empty_room_name_is_rejected():

    service = create_service()


    try:

        service.create_connection(
            room_name="",
        )


        assert False


    except ValueError:

        assert True