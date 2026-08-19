"""
Tests for Voice Speech Runtime.
"""

from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)

from app.providers.speech.speech_provider import (
    SpeechProvider,
)



class FakeSpeechProvider(
    SpeechProvider
):
    """
    Fake speech provider for testing.
    """


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

        return b"audio"



def test_voice_speech_runtime_transcription():

    runtime = VoiceSpeechRuntime(
        speech_provider=FakeSpeechProvider()
    )


    result = runtime.transcribe(
        audio=b"voice",
        language_code="fr",
    )


    assert result == "bonjour"



def test_voice_speech_runtime_synthesis():

    runtime = VoiceSpeechRuntime(
        speech_provider=FakeSpeechProvider()
    )


    result = runtime.synthesize(
        text="Bonjour",
        voice_profile="yeti",
        language_code="fr",
    )


    assert result == b"audio"