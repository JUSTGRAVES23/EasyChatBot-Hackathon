"""
Controlled real OpenAI speech-provider smoke test.

This test intentionally calls the real OpenAI API.

Run explicitly when OPENAI_API_KEY is configured.
"""

from __future__ import annotations


import os


from pathlib import Path


import pytest


from dotenv import load_dotenv


from app.providers.speech.openai_speech_provider import (
    OpenAISpeechProvider,
)


load_dotenv()



@pytest.mark.integration
def test_real_openai_speech_round_trip():

    if not os.getenv("OPENAI_API_KEY"):

        pytest.skip(
            "OPENAI_API_KEY is not configured."
        )


    audio_path = Path(
        "voice_smoke_test.wav"
    )


    if not audio_path.exists():

        pytest.fail(
            "voice_smoke_test.wav does not exist."
        )


    provider = (
        OpenAISpeechProvider()
    )


    audio = (
        audio_path
        .read_bytes()
    )


    transcription = (
        provider.transcribe(
            audio=audio,
            language_code="fr",
        )
    )


    assert isinstance(
        transcription,
        str,
    )


    speech = (
        provider.synthesize(
            text="Bonjour, je suis Yeti.",
            voice_profile="yeti",
            language_code="fr",
        )
    )


    assert isinstance(
        speech,
        bytes,
    )


    assert speech