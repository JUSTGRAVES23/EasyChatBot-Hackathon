"""
Tests for Speech Provider Configuration.
"""

import pytest


from app.configuration.providers.speech_provider_config import (
    SpeechProviderConfig,
)



def test_create_valid_speech_provider_config():

    config = SpeechProviderConfig(
        provider_name="openai",
        model_name="gpt-4o-mini-tts",
        default_language="fr",
    )


    assert config.provider_name == (
        "openai"
    )

    assert config.model_name == (
        "gpt-4o-mini-tts"
    )

    assert config.default_language == (
        "fr"
    )

    assert config.enabled is True



def test_empty_provider_name_is_rejected():

    with pytest.raises(
        ValueError
    ):

        SpeechProviderConfig(
            provider_name="",
            model_name="test-model",
            default_language="fr",
        )



def test_empty_model_name_is_rejected():

    with pytest.raises(
        ValueError
    ):

        SpeechProviderConfig(
            provider_name="openai",
            model_name="",
            default_language="fr",
        )



def test_empty_language_is_rejected():

    with pytest.raises(
        ValueError
    ):

        SpeechProviderConfig(
            provider_name="openai",
            model_name="test-model",
            default_language="",
        )