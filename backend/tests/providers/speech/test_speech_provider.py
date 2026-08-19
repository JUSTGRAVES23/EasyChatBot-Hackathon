"""
Tests for Speech Provider contract.
"""

from app.providers.speech.speech_provider import (
    SpeechProvider,
)



class FakeSpeechProvider(
    SpeechProvider
):
    """
    Test implementation.

    Simulates a real provider.
    """


    def transcribe(
        self,
        audio: bytes,
        language_code: str,
    ) -> str:
        """
        Fake speech-to-text.
        """

        return "bonjour"



    def synthesize(
        self,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        """
        Fake text-to-speech.
        """

        return b"audio-data"



def test_speech_provider_transcription():

    provider = FakeSpeechProvider()


    result = provider.transcribe(
        audio=b"sample-audio",
        language_code="fr",
    )


    assert result == (
        "bonjour"
    )



def test_speech_provider_synthesis():

    provider = FakeSpeechProvider()


    result = provider.synthesize(
        text="Bonjour",
        voice_profile="yeti",
        language_code="fr",
    )


    assert result == (
        b"audio-data"
    )