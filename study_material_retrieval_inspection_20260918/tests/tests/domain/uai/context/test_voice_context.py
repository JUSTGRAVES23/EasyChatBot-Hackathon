"""
Tests for VoiceContext.
"""

import pytest

from app.domain.uai.context.voice_context import (
    VoiceContext,
)


def test_create_voice_context():

    context = VoiceContext(
        language_code="fr",
        voice_provider="openai",
        voice_profile="yeti_fr",
    )

    assert context.voice_provider == "openai"


def test_empty_voice_provider_is_rejected():

    with pytest.raises(ValueError):

        VoiceContext(
            language_code="fr",
            voice_provider="",
            voice_profile="default",
        )