"""
LiveKit Realtime Agent Infrastructure.

Infrastructure boundary between LiveKit Agents and EasyChatBot.

Responsibilities:
- Define the LiveKit Agents character wrapper.
- Create an AgentSession.
- Keep LiveKit Agents implementation details inside infrastructure.
- Expose a small provider-independent application-facing boundary.
- Receive AI Runtime dependencies through composition.

Does NOT:
- Own EasyChatBot business logic.
- Manage call lifecycle state.
- Persist conversations.
- Modify production data.
- Bypass the EasyChatBot Runtime.
- Directly manage application authorization.
- Call LLM providers directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from livekit.agents import (
    Agent,
    AgentSession,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)



@dataclass(
    frozen=True,
    slots=True,
)
class LiveKitRealtimeAgent:
    """
    Infrastructure adapter for a LiveKit realtime character.

    The adapter creates the LiveKit Agents objects required for
    realtime voice execution while keeping EasyChatBot character
    context outside the LiveKit-specific implementation.

    LiveKit Agents remains an infrastructure/realtime boundary.

    EasyChatBot remains responsible for:
    - character logic
    - runtime orchestration
    - AI governance
    - provider selection
    """

    context: InteractionContext

    instructions: str

    conversation_runtime: ConversationRuntime | None = None



    def create_agent(
        self,
    ) -> Agent:
        """
        Create the LiveKit Agent representation
        of the character.

        The AI Runtime dependency is intentionally stored
        but not directly exposed to LiveKit yet.

        A dedicated LiveKit LLM adapter will translate:

            LiveKit LLM interface
                    |
                    v
            ConversationRuntime
                    |
                    v
            LLM Provider

        in the next integration step.
        """


        return Agent(
            instructions=self.instructions,
        )



    def create_session(
        self,
    ) -> AgentSession:
        """
        Create a LiveKit AgentSession.

        Provider-specific STT, LLM and TTS configuration
        remains outside this infrastructure wrapper.

        Future composition will inject:

        - STT provider
        - LLM adapter
        - TTS provider
        """

        return AgentSession()



    def character_id(
        self,
    ) -> str:
        """
        Return the active EasyChatBot character identifier.
        """


        return (
            self.context
            .character
            .character_id
        )



    def language_code(
        self,
    ) -> str:
        """
        Return the active interaction language.
        """


        return (
            self.context
            .world
            .language_code
        )



    def has_conversation_runtime(
        self,
    ) -> bool:
        """
        Check whether AI Runtime conversation
        capability is available.
        """


        return (
            self.conversation_runtime
            is not None
        )



__all__ = [
    "LiveKitRealtimeAgent",
]