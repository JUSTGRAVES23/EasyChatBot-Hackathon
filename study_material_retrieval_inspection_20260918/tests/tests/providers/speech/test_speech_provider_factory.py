"""
Tests for Speech Provider Factory.
"""

import pytest


from app.configuration.providers.speech_provider_config import (
    SpeechProviderConfig,
)


from app.providers.speech.speech_provider_factory import (
    SpeechProviderFactory,
)


from app.providers.speech.openai_speech_provider import (
    OpenAISpeechProvider,
)



def test_factory_creates_openai_provider():

    config = SpeechProviderConfig(
        provider_name="openai",
        model_name="gpt-4o-mini-tts",
        default_language="fr",
    )


    provider = (
        SpeechProviderFactory.create(
            config
        )
    )


    assert isinstance(
        provider,
        OpenAISpeechProvider,
    )



def test_factory_rejects_unknown_provider():

    config = SpeechProviderConfig(
        provider_name="unknown",
        model_name="unknown-model",
        default_language="fr",
    )


    with pytest.raises(
        ValueError,
        match="Unsupported speech provider",
    ):

        SpeechProviderFactory.create(
            config
        )