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

from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


class FakeFunctionalityControlService:
    """
    Minimal composition-level control dependency.
    """

    def get_availability(
        self,
        *,
        environment: str,
        functionality_id: str,
    ) -> str:
        return "enabled"


def test_create_voice_character_session_service():

    service = create_voice_character_session_service()

    assert isinstance(
        service,
        VoiceCharacterSessionService,
    )

    assert service.livekit_adapter is not None
    assert service.speech_runtime is not None


def test_create_voice_call_execution_service():

    service = create_voice_call_execution_service()

    assert isinstance(
        service,
        VoiceCallExecutionService,
    )

    assert service.execution_runtime is not None


def test_voice_character_session_composition_injects_control_service():

    control_service = FakeFunctionalityControlService()

    service = create_voice_character_session_service(
        functionality_control_service=control_service,
    )

    assert isinstance(
        service.speech_runtime,
        VoiceSpeechRuntime,
    )

    assert (
        service.speech_runtime.functionality_control_service
        is control_service
    )


def test_voice_character_session_composition_without_control_remains_compatible():

    service = create_voice_character_session_service()

    assert isinstance(
        service.speech_runtime,
        VoiceSpeechRuntime,
    )

    assert (
        service.speech_runtime.functionality_control_service
        is None
    )



