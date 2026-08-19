"""
Tests Voice Call Orchestrator runtime integration.

Validates that the orchestrator
creates a voice call session and
applies runtime preparation.
"""

from app.application.uai.voice.voice_call_orchestrator import (
    VoiceCallOrchestrator,
)


from app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)


from app.ai_runtime.voice.voice_call_runtime import (
    VoiceCallRuntime,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)


class FakeContextBuilder:
    """
    Fake context builder.

    Keeps test independent from
    infrastructure.
    """

    def build(
        self,
        *,
        learner,
        world_id,
        character_id,
        voice,
    ):
        from app.domain.uai.context.interaction_context import (
            InteractionContext,
        )

        from app.domain.uai.context.character_context import (
            CharacterContext,
        )

        from app.domain.uai.context.world_context import (
            WorldContext,
        )


        return InteractionContext(
            learner=learner,
            world=WorldContext(
                world_id=world_id,
                name="French World",
                language_code=voice.language_code,
                available_characters=[
                    character_id,
                ],
            ),
            character=CharacterContext(
                character_id=character_id,
                name="Yeti",
                personality_reference="storyteller",
                teaching_style="narrative",
            ),
            voice=voice,
        )



class FakeSessionService:
    """
    Fake character session service.
    """

    def create_session(
        self,
        *,
        context,
    ):
        from app.domain.uai.voice.voice_session import (
            VoiceSession,
        )

        return VoiceSession(
            session_id="session-001",
            room_name="yeti-room",
            character_id="yeti",
            language_code="fr",
        )



def test_orchestrator_prepares_runtime_voice_call():

    orchestrator = VoiceCallOrchestrator(
        context_builder=FakeContextBuilder(),
        session_service=FakeSessionService(),
        voice_runtime=VoiceCallRuntime(),
    )


    session = orchestrator.prepare_call(
        request=VoiceCallRequest(
            learner_id="learner-001",
            world_id="french_world",
            character_id="yeti",
            language_code="fr",
        )
    )


    assert session.session_id == (
        "session-001"
    )


    assert session.character_id == (
        "yeti"
    )


    assert session.state == (
        VoiceCallState.READY
    )