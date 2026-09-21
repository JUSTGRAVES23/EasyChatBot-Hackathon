"""
Tests for Voice Character Runtime.
"""

from app.ai_runtime.voice.voice_character_runtime import (
    VoiceCharacterRuntime,
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


from app.providers.speech.speech_provider import (
    SpeechProvider,
)



class FakeSpeechProvider(
    SpeechProvider
):
    """
    Fake speech provider.

    Captures runtime requests.
    """


    def __init__(self):

        self.last_voice_profile = None
        self.last_language_code = None
        self.last_text = None



    def transcribe(
        self,
        audio: bytes,
        language_code: str,
    ) -> str:

        return "bonjour"



    def synthesize(
        self,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:

        self.last_text = text

        self.last_voice_profile = (
            voice_profile
        )

        self.last_language_code = (
            language_code
        )

        return b"character-audio"



def create_context() -> InteractionContext:
    """
    Create Yeti interaction context.
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
                personality_reference=(
                    "storyteller"
                ),
                teaching_style=(
                    "narrative learning"
                ),
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



def test_character_runtime_generates_character_voice():

    provider = FakeSpeechProvider()


    speech_runtime = VoiceSpeechRuntime(
        speech_provider=provider
    )


    runtime = VoiceCharacterRuntime(
        context=create_context(),
        speech_runtime=speech_runtime,
    )


    audio = runtime.speak(
        "Bonjour, je suis Yeti."
    )


    assert audio == (
        b"character-audio"
    )


    assert runtime.character_id() == (
        "yeti"
    )


    assert provider.last_text == (
        "Bonjour, je suis Yeti."
    )


    assert provider.last_voice_profile == (
        "verse"
    )


    assert provider.last_language_code == (
        "fr"
    )


