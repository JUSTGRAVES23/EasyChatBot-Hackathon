"""
Tests for Voice Session domain model.
"""

import pytest

from app.domain.uai.voice.voice_session import (
    VoiceSession,
)


def test_create_valid_voice_session():

    session = VoiceSession(
        session_id="session-001",
        room_name="room-yeti-001",
        character_id="yeti",
        language_code="fr",
    )

    assert session.session_id == (
        "session-001"
    )

    assert session.room_name == (
        "room-yeti-001"
    )

    assert session.character_id == (
        "yeti"
    )

    assert session.language_code == (
        "fr"
    )

    assert session.status == (
        "created"
    )


def test_empty_session_id_is_rejected():

    with pytest.raises(
        ValueError,
        match="session_id cannot be empty.",
    ):

        VoiceSession(
            session_id="",
            room_name="room",
            character_id="yeti",
            language_code="fr",
        )


def test_empty_room_name_is_rejected():

    with pytest.raises(
        ValueError,
        match="room_name cannot be empty.",
    ):

        VoiceSession(
            session_id="session",
            room_name="",
            character_id="yeti",
            language_code="fr",
        )


def test_empty_character_id_is_rejected():

    with pytest.raises(
        ValueError,
        match="character_id cannot be empty.",
    ):

        VoiceSession(
            session_id="session",
            room_name="room",
            character_id="",
            language_code="fr",
        )


def test_empty_language_code_is_rejected():

    with pytest.raises(
        ValueError,
        match="language_code cannot be empty.",
    ):

        VoiceSession(
            session_id="session",
            room_name="room",
            character_id="yeti",
            language_code="",
        )


def test_voice_session_is_immutable():

    session = VoiceSession(
        session_id="session-001",
        room_name="room-yeti-001",
        character_id="yeti",
        language_code="fr",
    )

    with pytest.raises(
        Exception,
    ):

        session.status = "connected"