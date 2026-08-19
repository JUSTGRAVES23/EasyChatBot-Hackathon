"""
Tests for Voice Character Session Service.
"""

from app.application.uai.voice.voice_character_session_service import (
    VoiceCharacterSessionService,
)


from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


from app.domain.uai.context.character_context import (
    CharacterContext,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.domain.uai.context.learner_context import (
    LearnerContext,
)


from app.domain.uai.context.voice_context import (
    VoiceContext,
)


from app.domain.uai.context.world_context import (
    WorldContext,
)


from app.domain.uai.voice.voice_session import (
    VoiceSession,
)



class FakeLiveKitAdapter:
    """
    Fake LiveKit adapter.

    Matches production adapter contract.
    """


    def __init__(self):

        self.created_session = None



    def create_room_configuration(
        self,
        *,
        session: VoiceSession,
    ) -> dict[str, str]:
        """
        Prepare fake LiveKit configuration.
        """


        self.created_session = session


        return {
            "room_name": session.room_name,
            "character_id": session.character_id,
            "language_code": session.language_code,
            "provider": "livekit",
        }



class FakeSpeechProvider:
    """
    Fake speech provider.
    """

    pass



def create_context() -> InteractionContext:
    """
    Create test interaction context.
    """


    return InteractionContext(

        learner=(
            LearnerContext(
                learner_id="learner-001",
                learning_goals=[
                    "conversation",
                ],
            )
        ),

        world=(
            WorldContext(
                world_id="french_world",
                name="French World",
                language_code="fr",
                available_characters=[
                    "yeti",
                    "alix",
                ],
            )
        ),

        character=(
            CharacterContext(
                character_id="yeti",
                name="Yeti",
                personality_reference="storyteller",
                teaching_style="narrative learning",
            )
        ),

        voice=(
            VoiceContext(
                language_code="fr",
                voice_provider="openai",
                voice_profile="verse",
            )
        ),
    )



def test_create_character_voice_session():

    livekit_adapter = FakeLiveKitAdapter()


    speech_runtime = VoiceSpeechRuntime(
        speech_provider=FakeSpeechProvider()
    )


    service = VoiceCharacterSessionService(
        livekit_adapter=livekit_adapter,
        speech_runtime=speech_runtime,
    )


    session = service.create_session(
        context=create_context()
    )


    assert session.character_id == (
        "yeti"
    )


    assert session.language_code == (
        "fr"
    )


    assert session.room_name == (
        "yeti-voice-room"
    )


    assert livekit_adapter.created_session is not None


    assert (
        livekit_adapter
        .created_session
        .character_id
        ==
        "yeti"
    )