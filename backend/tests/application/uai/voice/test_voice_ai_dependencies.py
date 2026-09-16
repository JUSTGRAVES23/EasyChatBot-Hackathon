"""
Tests for realtime voice AI dependency composition.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)
from app.application.uai.voice.voice_ai_dependencies import (
    build_voice_speech_runtime,
)


def test_build_voice_speech_runtime_uses_openai_gpt4o_mini_tts():
    provider = Mock()

    with patch(
        "backend.app.application.uai.voice.voice_ai_dependencies."
        "SpeechProviderFactory.create",
        return_value=provider,
    ) as create_provider:

        runtime = build_voice_speech_runtime()

    assert isinstance(
        runtime,
        VoiceSpeechRuntime,
    )

    create_provider.assert_called_once()

    config = create_provider.call_args.args[0]

    assert config.provider_name == "openai"
    assert config.model_name == "gpt-4o-mini-tts"
    assert config.default_language == "fr"


def test_build_voice_speech_runtime_injects_functionality_control():
    provider = Mock()
    control_service = Mock()

    with patch(
        "backend.app.application.uai.voice.voice_ai_dependencies."
        "SpeechProviderFactory.create",
        return_value=provider,
    ):

        runtime = build_voice_speech_runtime(
            functionality_control_service=control_service,
        )

    assert (
        runtime.functionality_control_service
        is control_service
    )
    assert runtime.speech_provider is provider
