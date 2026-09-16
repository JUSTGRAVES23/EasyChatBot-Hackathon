"""
Voice AI dependency composition.

Builds AI Runtime dependencies required
by realtime voice execution.

Responsibilities:
- Compose conversation runtime.
- Compose speech runtime.
- Keep provider selection outside infrastructure.
- Provide application-ready dependencies.

Does NOT:
- Execute calls.
- Handle HTTP.
- Manage LiveKit rooms.
- Store secrets.
- Call providers directly.
"""

from __future__ import annotations


from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)


from app.ai_runtime.voice.functionality_control_port import (
    FunctionalityControlPort,
)

from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


from app.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)


from app.providers.speech.speech_provider_factory import (
    SpeechProviderFactory,
)


from app.configuration.providers.speech_provider_config import (
    SpeechProviderConfig,
)



def build_conversation_runtime() -> ConversationRuntime:
    """
    Build EasyChatBot AI conversation runtime.
    """

    provider = (
        LLMProviderFactory.create()
    )


    return ConversationRuntime(
        llm_provider=provider,
    )



def build_voice_speech_runtime(
    *,
    functionality_control_service: FunctionalityControlPort | None = None,
) -> VoiceSpeechRuntime:
    """
    Build EasyChatBot voice speech runtime.

    The operational-control dependency is injected through
    the runtime port so the AI Runtime remains independent
    from the application control-service implementation.
    """

    config = SpeechProviderConfig(
        provider_name="openai",
        model_name="gpt-4o-mini-tts",
        default_language="fr",
    )


    provider = (
        SpeechProviderFactory.create(
            config,
        )
    )


    return VoiceSpeechRuntime(
        speech_provider=provider,
        functionality_control_service=(
            functionality_control_service
        ),
    )



__all__ = [
    "build_conversation_runtime",
    "build_voice_speech_runtime",
]
