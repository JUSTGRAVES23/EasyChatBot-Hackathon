"""LiveKit realtime agent infrastructure."""

from __future__ import annotations

from dataclasses import dataclass

from livekit.agents import Agent, AgentSession

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)
from app.domain.uai.context.interaction_context import (
    InteractionContext,
)
from app.infrastructure.voice.livekit_conversation_llm import (
    LiveKitConversationLLM,
)
from app.infrastructure.voice.livekit_stt_adapter import (
    LiveKitSTTAdapter,
)
from app.infrastructure.voice.livekit_tts_adapter import (
    LiveKitTTSAdapter,
)


@dataclass(frozen=True, slots=True)
class LiveKitRealtimeAgent:
    """Infrastructure adapter for a LiveKit realtime character."""

    context: InteractionContext
    instructions: str
    conversation_runtime: ConversationRuntime | None = None
    speech_runtime: VoiceSpeechRuntime | None = None

    def create_agent(self) -> Agent:
        """Create the LiveKit character agent."""

        return Agent(
            instructions=self.instructions,
        )

    def create_session(self) -> AgentSession:
        """Create a LiveKit session with EasyChatBot AI adapters."""

        if self.conversation_runtime is None:
            raise RuntimeError(
                "ConversationRuntime is required "
                "for a LiveKit realtime session."
            )

        if self.speech_runtime is None:
            raise RuntimeError(
                "VoiceSpeechRuntime is required "
                "for a LiveKit realtime session."
            )

        llm_adapter = LiveKitConversationLLM(
            conversation_runtime=self.conversation_runtime,
            character_instruction=self.instructions,
        )

        stt_adapter = LiveKitSTTAdapter(
            speech_runtime=self.speech_runtime,
            language_code=self.language_code(),
        )

        tts_adapter = LiveKitTTSAdapter(
            speech_runtime=self.speech_runtime,
            voice_profile=self.context.voice.voice_profile,
            language_code=self.language_code(),
        )

        return AgentSession(
            stt=stt_adapter,
            llm=llm_adapter,
            tts=tts_adapter,
        )

    def character_id(self) -> str:
        """Return the active EasyChatBot character identifier."""

        return self.context.character.character_id

    def language_code(self) -> str:
        """Return the active voice language."""

        return self.context.voice.language_code

    def has_conversation_runtime(self) -> bool:
        """Check whether conversation runtime is available."""

        return self.conversation_runtime is not None


__all__ = ["LiveKitRealtimeAgent"]
