"""
Tests for Voice Call Context Factory.
"""

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)

from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)

from app.domain.uai.voice.voice_call import (
    VoiceCall,
)

from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)


def create_request() -> VoiceCallRequest:
    """
    Create a standard test request.
    """

    return VoiceCallRequest(
        learner_id="learner-001",
        world_id="french_world",
        character_id="yeti",
        language_code="fr",
    )


def test_create_execution_context():
    """
    Factory creates an execution context.
    """

    factory = VoiceCallContextFactory()

    context = factory.create(
        request=create_request(),
    )

    assert context is not None
    assert context.session is not None
    assert context.room is not None


def test_created_session_starts_ready():
    """
    Newly created execution sessions start READY.
    """

    factory = VoiceCallContextFactory()

    context = factory.create(
        request=create_request(),
    )

    assert context.session.state == (
        VoiceCallState.READY
    )


def test_context_contains_learner_and_character():
    """
    Execution context contains the request identity.
    """

    factory = VoiceCallContextFactory()

    context = factory.create(
        request=create_request(),
    )

    assert context.session.learner_id == (
        "learner-001"
    )

    assert context.session.character_id == (
        "yeti"
    )

    assert context.session.world_id == (
        "french_world"
    )

    assert context.session.language_code == (
        "fr"
    )


def test_room_identity_matches_session():
    """
    Room identity matches the execution session.
    """

    factory = VoiceCallContextFactory()

    context = factory.create(
        request=create_request(),
    )

    assert context.room.room_id == (
        context.session.session_id
    )


def test_create_execution_context_without_persistent_voice_call():
    """
    Existing request-only callers remain compatible.

    The persistent VoiceCall identity is optional
    at this application boundary.
    """

    factory = VoiceCallContextFactory()

    context = factory.create(
        request=create_request(),
    )

    assert context.voice_call is None
    assert context.has_voice_identity() is False


def test_create_execution_context_preserves_persistent_voice_call_identity():
    """
    A supplied persistent VoiceCall remains attached
    to the execution context.
    """

    factory = VoiceCallContextFactory()

    now = datetime.now(timezone.utc)

    voice_call = VoiceCall(
        id="vc-001",
        learner_id="learner-001",
        character_id="yeti",
        world_id="french_world",
        language_code="fr",
        state=VoiceCallState.CREATED,
        created_at=now,
        expires_at=(
            now
            + timedelta(minutes=30)
        ),
    )

    context = factory.create(
        request=create_request(),
        voice_call=voice_call,
    )

    assert context.voice_call is voice_call
    assert context.voice_call.id == "vc-001"
    assert context.has_voice_identity() is True


