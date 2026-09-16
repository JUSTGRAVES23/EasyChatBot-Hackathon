"""
Tests for LiveKit Token Service.

Validates the real LiveKit infrastructure adapter.

Responsibilities tested:
- Real JWT generation.
- Room binding.
- Provider identity.
- Participant identity.
- Expiration handling.
- Input validation.
"""

from __future__ import annotations


from datetime import (
    datetime,
    timezone,
)


import base64
import json


import pytest


from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)


from app.infrastructure.voice.livekit_token_service import (
    LiveKitTokenService,
)



def decode_jwt_payload(
    token: str,
) -> dict:
    """
    Decode the JWT payload without verifying
    the signature.

    Signature verification belongs to LiveKit.
    These tests only validate the claims generated
    by our infrastructure adapter.
    """

    parts = token.split(".")

    assert len(parts) == 3

    payload = parts[1]

    padding = (
        "="
        * (
            4
            - len(payload) % 4
        )
    )

    decoded = base64.urlsafe_b64decode(
        payload + padding
    )

    return json.loads(
        decoded.decode("utf-8")
    )



def test_create_livekit_token():

    service = (
        LiveKitTokenService()
    )


    token = (
        service.create_token(
            room_name="yeti-room-001",
        )
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


    # A real LiveKit JWT is generated.
    assert token.token.count(".") == 2


    assert token.token.startswith(
        "eyJ"
    )


    payload = (
        decode_jwt_payload(
            token.token
        )
    )


    assert payload["sub"].startswith(
        "learner-"
    )


    assert payload["video"]["roomJoin"] is True


    assert payload["video"]["room"] == (
        "yeti-room-001"
    )



def test_custom_expiration_time():

    service = (
        LiveKitTokenService()
    )


    token = (
        service.create_token(
            room_name="room-001",
            expires_minutes=60,
        )
    )


    now = (
        datetime.now(
            timezone.utc
        )
    )


    assert token.expires_at > (
        now
    )


    remaining_seconds = (
        token.expires_at - now
    ).total_seconds()


    # Allow a small execution-time tolerance.
    assert 3500 < (
        remaining_seconds
    ) <= 3600


    payload = (
        decode_jwt_payload(
            token.token
        )
    )


    assert payload["exp"] > (
        payload["nbf"]
    )



def test_empty_room_name_is_rejected():

    service = (
        LiveKitTokenService()
    )


    with pytest.raises(
        ValueError,
        match="room_name cannot be empty",
    ):

        service.create_token(
            room_name="",
        )



def test_invalid_expiration_is_rejected():

    service = (
        LiveKitTokenService()
    )


    with pytest.raises(
        ValueError,
        match="expires_minutes must be positive",
    ):

        service.create_token(
            room_name="room-001",
            expires_minutes=0,
        )




