"""
Tests for Voice Connection Service.

Validates the application boundary
for creating voice connection credentials.

The application test must not depend
on LiveKit infrastructure.
"""

from datetime import datetime, timedelta, timezone

from app.application.uai.voice.voice_connection_service import (
    VoiceConnectionService,
)
from app.domain.uai.voice.voice_connection_token import (
    VoiceConnectionToken,
)


class FakeVoiceConnectionPort:
    """
    Test double for VoiceConnectionPort.

    No LiveKit SDK or JWT generation is used.
    """

    def create_connection_token(
        self,
        *,
        room_name: str,
        identity: str | None = None,
        expires_minutes: int = 30,
    ) -> VoiceConnectionToken:
        return VoiceConnectionToken(
            token="test-token",
            room_name=room_name,
            provider="test",
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=expires_minutes)
            ),
        )


def create_service() -> VoiceConnectionService:
    return VoiceConnectionService(
        token_service=FakeVoiceConnectionPort(),
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
    assert token.room_name == "yeti-room-001"
    assert token.provider == "test"
    assert token.token == "test-token"
    assert token.expires_at is not None


def test_create_connection_passes_identity():
    class CapturingVoiceConnectionPort:
        def __init__(self) -> None:
            self.identity = None
            self.expires_minutes = None

        def create_connection_token(
            self,
            *,
            room_name: str,
            identity: str | None = None,
            expires_minutes: int = 30,
        ) -> VoiceConnectionToken:
            self.identity = identity
            self.expires_minutes = expires_minutes

            return VoiceConnectionToken(
                token="test-token",
                room_name=room_name,
                provider="test",
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(
                        minutes=expires_minutes,
                    )
                ),
            )

    port = CapturingVoiceConnectionPort()

    service = VoiceConnectionService(
        token_service=port,
    )

    service.create_connection(
        room_name="room-001",
        identity="learner-001",
        expires_minutes=15,
    )

    assert port.identity == "learner-001"
    assert port.expires_minutes == 15


def test_connection_token_has_provider_independent_expiration():
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


def test_invalid_expiration_is_rejected():
    service = create_service()

    try:
        service.create_connection(
            room_name="room-001",
            expires_minutes=0,
        )
        assert False
    except ValueError:
        assert True


def test_empty_identity_is_rejected():
    service = create_service()

    try:
        service.create_connection(
            room_name="room-001",
            identity="",
        )
        assert False
    except ValueError:
        assert True

