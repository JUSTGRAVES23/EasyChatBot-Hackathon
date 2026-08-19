"""
Tests for OpenAI Speech Provider adapter.
"""

import pytest


from app.providers.speech.speech_provider import (
    SpeechProvider,
)

from app.providers.speech.openai_speech_provider import (
    OpenAISpeechProvider,
)



def test_openai_provider_implements_contract():

    provider = OpenAISpeechProvider()


    assert isinstance(
        provider,
        SpeechProvider,
    )



def test_openai_provider_transcription_not_ready():

    provider = OpenAISpeechProvider()


    with pytest.raises(
        NotImplementedError
    ):

        provider.transcribe(
            audio=b"test-audio",
            language_code="fr",
        )



def test_openai_provider_synthesis_not_ready():

    provider = OpenAISpeechProvider()


    with pytest.raises(
        NotImplementedError
    ):

        provider.synthesize(
            text="Bonjour",
            voice_profile="yeti",
            language_code="fr",
        )