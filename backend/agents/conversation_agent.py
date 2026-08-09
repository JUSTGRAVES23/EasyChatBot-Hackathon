"""
Conversation Agent.

Coordinates AI companion conversations.

The Conversation Agent uses the approved
CharacterProfile to shape the response.

It does not directly call external providers.
"""

from backend.agents.base_agent import BaseAgent
from backend.agents.agent_manifest import AgentManifest
from backend.agents.agent_result import AgentResult

from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from backend.characters.character_profile import (
    CharacterProfile,
)


class ConversationAgent(BaseAgent):
    """
    Agent responsible for companion conversations.
    """

    def __init__(
        self,
        character: CharacterProfile,
    ):
        """
        Initialise conversation agent.

        Args:
            character:
                Approved AI companion identity and behaviour.
        """

        super().__init__(
            AgentManifest(
                agent_id="conversation_agent",
                name="Conversation Agent",
                description=(
                    "Creates personalised AI companion "
                    "conversations."
                ),
            )
        )

        self.character = character

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        """
        Generate a character-aware companion response.
        """

        response = (
            f"{self.character.name}: "
            f"Let's explore this together. "
            f"You asked: {context.request}"
        )

        return AgentResult(
            success=True,
            agent_id=self.manifest.agent_id,
            output={
                "character": self.character.name,
                "personality": (
                    self.character.personality
                ),
                "learning_style": (
                    self.character.learning_style
                ),
                "message": response,
            },
        )