"""
Conversation Agent.

Provides character-aware conversational responses
for the EasyChatBot hackathon runtime.

The agent is intentionally lightweight.

The main EasyChatBot repository already contains
the production conversation and voice architecture.
This hackathon agent exists as a runtime demonstration
and contract-compatible prototype.

Architecture:

ExecutionContext
|
v
ConversationAgent
|
+--> CharacterProfile
|
+--> Optional IntelligenceContext
|
v
AgentResult
"""

from __future__ import annotations

from backend.agents.agent_manifest import (
    AgentManifest,
)

from backend.agents.agent_result import (
    AgentResult,
)

from backend.agents.base_agent import (
    BaseAgent,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)


class ConversationAgent(BaseAgent):
    """
    Character-aware conversation agent.

    The agent uses the supplied CharacterProfile to
    construct a deterministic conversation response.

    When live intelligence is available through the
    ExecutionContext, it is exposed as structured
    conversation context.

    This implementation deliberately does not introduce
    another LLM provider or voice system.
    """

    def __init__(
        self,
        character: CharacterProfile,
    ) -> None:
        super().__init__(
            AgentManifest(
                agent_id="conversation_agent",
                name="Conversation Agent",
                description=(
                    "Provides character-aware "
                    "conversation responses."
                ),
            )
        )

        self.character = character

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Execute the conversation agent.

        Args:
            context:
                Runtime execution context containing
                the user's request and optional
                live intelligence context.

        Returns:
            AgentResult containing the character
            conversation response.
        """

        output = {
            "character": self.character.name,
            "personality": self.character.personality,
            "learning_style": (
                self.character.learning_style
            ),
            "message": (
                f"{self.character.name}: "
                f"Let's explore this together. "
                f"You asked: {context.request}"
            ),
            "intelligence_context": None,
        }

        if context.has_intelligence_context:
            output["intelligence_context"] = (
                context.intelligence_context.to_context_text()
            )

        return AgentResult(
            success=True,
            agent_id=self.manifest.agent_id,
            output=output,
        )