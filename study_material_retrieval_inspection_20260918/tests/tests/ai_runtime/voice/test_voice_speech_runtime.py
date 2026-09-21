"""
Tests for Voice Speech Runtime.
"""

import pytest

from app.ai_runtime.voice.voice_speech_runtime import VoiceSpeechRuntime
from app.providers.speech.speech_provider import SpeechProvider


class FakeSpeechProvider(SpeechProvider):
    """
    Fake speech provider for testing.
    """

    def __init__(self):
        self.transcribe_calls = 0
        self.synthesize_calls = 0

    def transcribe(
        self,
        audio: bytes,
        language_code: str,
    ) -> str:
        self.transcribe_calls += 1
        return "bonjour"

    def synthesize(
        self,
        text: str,
        voice_profile: str,
        language_code: str,
    ) -> bytes:
        self.synthesize_calls += 1
        return b"audio"


class FakeFunctionalityControlService:
    """
    Minimal operational-control test double.
    """

    def __init__(
        self,
        *,
        availability: str = "enabled",
        error: Exception | None = None,
    ):
        self.availability = availability
        self.error = error
        self.calls = []

    def get_availability(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> str:
        self.calls.append(
            {
                "environment": environment,
                "functionality_id": functionality_id,
            }
        )

        if self.error is not None:
            raise self.error

        return self.availability


def test_voice_speech_runtime_transcription():
    provider = FakeSpeechProvider()

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
    )

    result = runtime.transcribe(
        audio=b"voice",
        language_code="fr",
    )

    assert result == "bonjour"
    assert provider.transcribe_calls == 1


def test_voice_speech_runtime_synthesis():
    provider = FakeSpeechProvider()

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
    )

    result = runtime.synthesize(
        text="Bonjour",
        voice_profile="yeti",
        language_code="fr",
    )

    assert result == b"audio"
    assert provider.synthesize_calls == 1


def test_enabled_functionality_allows_synthesis():
    provider = FakeSpeechProvider()
    control = FakeFunctionalityControlService(
        availability="enabled",
    )

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
        functionality_control_service=control,
    )

    result = runtime.synthesize(
        text="Bonjour",
        voice_profile="yeti",
        language_code="fr",
    )

    assert result == b"audio"
    assert provider.synthesize_calls == 1
    assert control.calls == [
        {
            "environment": "adults",
            "functionality_id": "voice_tts",
        }
    ]


def test_disabled_functionality_blocks_synthesis():
    provider = FakeSpeechProvider()
    control = FakeFunctionalityControlService(
        availability="disabled",
    )

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
        functionality_control_service=control,
    )

    with pytest.raises(
        RuntimeError,
        match="Voice/TTS functionality is currently unavailable",
    ):
        runtime.synthesize(
            text="Bonjour",
            voice_profile="yeti",
            language_code="fr",
        )

    assert provider.synthesize_calls == 0


def test_disabled_functionality_blocks_transcription():
    provider = FakeSpeechProvider()
    control = FakeFunctionalityControlService(
        availability="disabled",
    )

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
        functionality_control_service=control,
    )

    with pytest.raises(
        RuntimeError,
        match="Voice/TTS functionality is currently unavailable",
    ):
        runtime.transcribe(
            audio=b"voice",
            language_code="fr",
        )

    assert provider.transcribe_calls == 0


def test_control_lookup_failure_fails_closed():
    provider = FakeSpeechProvider()
    control = FakeFunctionalityControlService(
        error=RuntimeError("control unavailable"),
    )

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
        functionality_control_service=control,
    )

    with pytest.raises(
        RuntimeError,
        match="Voice/TTS operational control could not be verified",
    ):
        runtime.synthesize(
            text="Bonjour",
            voice_profile="yeti",
            language_code="fr",
        )

    assert provider.synthesize_calls == 0


def test_runtime_without_control_preserves_lower_level_compatibility():
    provider = FakeSpeechProvider()

    runtime = VoiceSpeechRuntime(
        speech_provider=provider,
    )

    assert runtime.synthesize(
        text="Bonjour",
        voice_profile="yeti",
        language_code="fr",
    ) == b"audio"

    assert provider.synthesize_calls == 1



