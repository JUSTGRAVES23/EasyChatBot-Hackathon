"""
Tests for Voice Connection Token domain model.

Validates that voice connection
credentials are represented as valid
immutable domain state.
"""

from datetime import datetime, timedelta


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)



def create_valid_token() -> VoiceConnectionToken:
    """
    Create valid test token.
    """

    return VoiceConnectionToken(
        token="token-001",
        room_name="yeti-room-001",
        provider="livekit",
        expires_at=(
            datetime.utcnow()
            + timedelta(
                minutes=30
            )
        ),
    )



def test_create_voice_connection_token():

    token = create_valid_token()


    assert token.token == (
        "token-001"
    )


    assert token.room_name == (
        "yeti-room-001"
    )


    assert token.provider == (
        "livekit"
    )



def test_future_expiration_is_required():

    token = create_valid_token()


    assert token.expires_at > (
        datetime.utcnow()
    )



def test_empty_token_is_rejected():

    try:

        VoiceConnectionToken(
            token="",
            room_name="room-001",
            provider="livekit",
            expires_at=(
                datetime.utcnow()
                + timedelta(
                    minutes=30
                )
            ),
        )


        assert False


    except ValueError:

        assert True



def test_empty_room_name_is_rejected():

    try:

        VoiceConnectionToken(
            token="token-001",
            room_name="",
            provider="livekit",
            expires_at=(
                datetime.utcnow()
                + timedelta(
                    minutes=30
                )
            ),
        )


        assert False


    except ValueError:

        assert True



def test_expired_token_is_rejected():

    try:

        VoiceConnectionToken(
            token="token-001",
            room_name="room-001",
            provider="livekit",
            expires_at=(
                datetime.utcnow()
                - timedelta(
                    minutes=1
                )
            ),
        )


        assert False


    except ValueError:

        assert True