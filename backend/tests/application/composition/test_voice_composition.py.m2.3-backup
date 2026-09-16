"""
Tests for Voice Composition Root.
"""

from app.application.composition.voice_composition import (
    create_voice_character_session_service,
    create_voice_call_execution_service,
)


from app.application.uai.voice.voice_character_session_service import (
    VoiceCharacterSessionService,
)


from app.application.uai.voice.voice_call_execution_service import (
    VoiceCallExecutionService,
)


def test_create_voice_character_session_service():

    service = (
        create_voice_character_session_service()
    )


    assert isinstance(
        service,
        VoiceCharacterSessionService,
    )


    assert service.livekit_adapter is not None


    assert service.speech_runtime is not None



def test_create_voice_call_execution_service():

    service = (
        create_voice_call_execution_service()
    )


    assert isinstance(
        service,
        VoiceCallExecutionService,
    )


    assert service.execution_runtime is not None