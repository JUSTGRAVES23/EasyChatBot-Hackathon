"""
LiveKit Voice Composition.

Application composition boundary for
creating realtime voice agents.

Responsibilities:
- Build EasyChatBot realtime voice dependencies.
- Convert validated voice context into
  the LiveKit realtime infrastructure adapter.
- Keep LiveKit-specific construction
  outside application services.

Does NOT:
- Handle HTTP.
- Connect to LiveKit rooms.
- Execute the LiveKit worker.
- Persist data.
- Select learners or characters.
- Bypass the EasyChatBot Runtime.
"""

from __future__ import annotations


from app.ai_runtime.voice.voice_character_agent import (
    VoiceCharacterAgent,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.infrastructure.voice.livekit_realtime_agent import (
    LiveKitRealtimeAgent,
)



def create_livekit_realtime_agent(
    *,
    context: InteractionContext,
    instructions: str,
) -> LiveKitRealtimeAgent:
    """
    Create the LiveKit realtime infrastructure adapter.

    The InteractionContext is supplied by the
    existing EasyChatBot application/runtime layer.

    LiveKit remains an infrastructure boundary.
    """

    return LiveKitRealtimeAgent(
        context=context,
        instructions=instructions,
    )



__all__ = [
    "create_livekit_realtime_agent",
]

