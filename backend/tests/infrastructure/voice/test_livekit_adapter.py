"""
Tests for LiveKit Infrastructure Adapter.
"""

from app.domain.uai.voice.voice_session import (
    VoiceSession,
)

from app.infrastructure.voice.livekit_adapter import (
    LiveKitAdapter,
)


def test_create_room_configuration():

    adapter = LiveKitAdapter()


    session = VoiceSession(
        session_id="session-001",
        room_name="yeti-session-001",
        character_id="yeti",
        language_code="fr",
    )


    configuration = (
        adapter.create_room_configuration(
            session=session,
        )
    )


    assert configuration["room_name"] == (
        "yeti-session-001"
    )


    assert configuration["character_id"] == (
        "yeti"
    )


    assert configuration["language_code"] == (
        "fr"
    )


    assert configuration["provider"] == (
        "livekit"
    )