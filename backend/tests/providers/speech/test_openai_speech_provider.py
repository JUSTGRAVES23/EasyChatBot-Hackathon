"""
Tests for OpenAI Speech Provider adapter.

These tests validate the provider boundary without
calling the real OpenAI API.
"""

from types import SimpleNamespace


from app.providers.speech.speech_provider import (
    SpeechProvider,
)


from app.providers.speech.openai_speech_provider import (
    OpenAISpeechProvider,
)



class FakeTranscriptions:

    def __init__(
        self,
        response,
    ):
        self.response = response
        self.last_kwargs = None


    def create(
        self,
        **kwargs,
    ):
        self.last_kwargs = kwargs

        return self.response



class FakeSpeech:

    def __init__(
        self,
        response,
    ):
        self.response = response
        self.last_kwargs = None


    def create(
        self,
        **kwargs,
    ):
        self.last_kwargs = kwargs

        return self.response



class FakeAudio:

    def __init__(
        self,
        transcription_response,
        speech_response,
    ):
        self.transcriptions = (
            FakeTranscriptions(
                transcription_response,
            )
        )

        self.speech = (
            FakeSpeech(
                speech_response,
            )
        )



class FakeOpenAIClient:

    def __init__(
        self,
        transcription_response=None,
        speech_response=None,
    ):
        self.audio = FakeAudio(
            transcription_response=(
                transcription_response
            ),
            speech_response=(
                speech_response
            ),
        )



def test_openai_provider_implements_contract():

    provider = (
        OpenAISpeechProvider()
    )


    assert isinstance(
        provider,
        SpeechProvider,
    )



def test_transcribe_calls_openai():

    client = FakeOpenAIClient(
        transcription_response=(
            SimpleNamespace(
                text="Bonjour Yeti",
            )
        ),
    )


    provider = (
        OpenAISpeechProvider(
            client=client,
        )
    )


    result = provider.transcribe(
        audio=b"test-audio",
        language_code="fr",
    )


    assert result == (
        "Bonjour Yeti"
    )


    request = (
        client
        .audio
        .transcriptions
        .last_kwargs
    )


    assert request["model"] == (
        "gpt-4o-mini-transcribe"
    )


    assert request["language"] == (
        "fr"
    )


    assert request["file"].name == (
        "voice_input.wav"
    )



def test_synthesize_calls_openai():

    client = FakeOpenAIClient(
        speech_response=(
            SimpleNamespace(
                content=b"audio-data",
            )
        ),
    )


    provider = (
        OpenAISpeechProvider(
            client=client,
        )
    )


    result = provider.synthesize(
        text="Bonjour",
        voice_profile="yeti",
        language_code="fr",
    )


    assert result == (
        b"audio-data"
    )


    request = (
        client
        .audio
        .speech
        .last_kwargs
    )


    assert request["model"] == (
        "gpt-4o-mini-tts"
    )


    assert request["voice"] == (
        "onyx"
    )


    assert request["input"] == (
        "Bonjour"
    )



def test_unknown_voice_profile_uses_default_voice():

    client = FakeOpenAIClient(
        speech_response=(
            SimpleNamespace(
                content=b"audio-data",
            )
        ),
    )


    provider = (
        OpenAISpeechProvider(
            client=client,
        )
    )


    provider.synthesize(
        text="Bonjour",
        voice_profile="unknown-character",
        language_code="fr",
    )


    request = (
        client
        .audio
        .speech
        .last_kwargs
    )


    assert request["voice"] == (
        "alloy"
    )



def test_empty_audio_is_rejected():

    provider = (
        OpenAISpeechProvider()
    )


    try:

        provider.transcribe(
            audio=b"",
            language_code="fr",
        )

        assert False

    except ValueError as exc:

        assert str(exc) == (
            "audio cannot be empty."
        )



def test_empty_language_is_rejected():

    provider = (
        OpenAISpeechProvider()
    )


    try:

        provider.transcribe(
            audio=b"audio",
            language_code="",
        )

        assert False

    except ValueError as exc:

        assert str(exc) == (
            "language_code cannot be empty."
        )



def test_empty_text_is_rejected():

    provider = (
        OpenAISpeechProvider()
    )


    try:

        provider.synthesize(
            text="",
            voice_profile="yeti",
            language_code="fr",
        )

        assert False

    except ValueError as exc:

        assert str(exc) == (
            "text cannot be empty."
        )



def test_empty_voice_profile_is_rejected():

    provider = (
        OpenAISpeechProvider()
    )


    try:

        provider.synthesize(
            text="Bonjour",
            voice_profile="",
            language_code="fr",
        )

        assert False

    except ValueError as exc:

        assert str(exc) == (
            "voice_profile cannot be empty."
        )