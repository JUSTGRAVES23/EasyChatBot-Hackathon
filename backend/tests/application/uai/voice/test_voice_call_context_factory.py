"""
Tests for Voice Call Context Factory.

Validates that voice call requests are
converted into a valid execution context.
"""

from app.application.uai.voice.voice_call_context_factory import (
    VoiceCallContextFactory,
)


from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceParticipantRole,
)



def create_request() -> VoiceCallRequest:
    """
    Create test voice call request.
    """

    return VoiceCallRequest(
        learner_id="learner-001",
        world_id="french_world",
        character_id="yeti",
        language_code="fr",
    )



def test_create_execution_context():

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



def test_created_session_starts_ready():

    factory = VoiceCallContextFactory()


    context = factory.create(
        request=create_request(),
    )


    assert context.session.state == (
        VoiceCallState.READY
    )



def test_context_contains_learner_and_character():

    factory = VoiceCallContextFactory()


    context = factory.create(
        request=create_request(),
    )


    roles = [
        participant.role
        for participant
        in context.room.participants
    ]


    assert (
        VoiceParticipantRole.LEARNER
        in roles
    )


    assert (
        VoiceParticipantRole.CHARACTER
        in roles
    )



def test_room_identity_matches_session():

    factory = VoiceCallContextFactory()


    context = factory.create(
        request=create_request(),
    )


    assert context.room.room_id == (
        context.session.session_id
    )