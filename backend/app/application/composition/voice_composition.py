"""
Voice Composition Root.

Central place where voice dependencies
are assembled.

Responsibilities:
- Create runtime dependencies.
- Wire providers.
- Wire operational controls.
- Return ready application services.

Does NOT:
- Handle HTTP.
- Execute calls.
- Store user data.
"""

from __future__ import annotations

from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
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
from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)
from app.providers.speech.speech_provider_factory import (
    SpeechProviderFactory,
)
from app.configuration.providers.speech_provider_config import (
    SpeechProviderConfig,
)
from app.infrastructure.voice.livekit_adapter import (
    LiveKitAdapter,
)


def create_voice_character_session_service(
    functionality_control_service: (
        FunctionalityOperationalControlService | None
    ) = None,
) -> VoiceCharacterSessionService:
    """
    Build voice session application service.

    The operational-control service is injected from
    the application composition root when available.
    """

    provider_config = SpeechProviderConfig(
        provider_name="openai",
        model_name="gpt-4o-mini-tts",
        default_language="fr",
    )

    speech_provider = SpeechProviderFactory.create(
        provider_config
    )

    speech_runtime = VoiceSpeechRuntime(
        speech_provider=speech_provider,
        functionality_control_service=functionality_control_service,
    )

    livekit_adapter = LiveKitAdapter()

    return VoiceCharacterSessionService(
        livekit_adapter=livekit_adapter,
        speech_runtime=speech_runtime,
    )


def create_voice_call_execution_service(
) -> VoiceCallExecutionService:
    """
    Build voice call execution service.
    """

    execution_runtime = VoiceCallExecutionRuntime()

    return VoiceCallExecutionService(
        execution_runtime=execution_runtime,
    )


__all__ = [
    "create_voice_character_session_service",
    "create_voice_call_execution_service",
]


