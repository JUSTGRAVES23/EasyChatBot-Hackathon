"""
Companion Service.

Coordinates:

Character
Conversation Agent
Research Agent
Quality Agent
Memory Service

Application orchestration layer.

Live Intelligence flow:

CompanionService
        |
        +--> ResearchAgent
        |        |
        |        v
        |   IntelligenceContext
        |
        +--> ConversationAgent
                 ^
                 |
          enriched ExecutionContext
"""

from __future__ import annotations

from dataclasses import replace

from backend.agents.conversation_agent import (
    ConversationAgent,
)

from backend.agents.research_agent import (
    ResearchAgent,
)

from backend.agents.quality_agent import (
    QualityAgent,
)

from backend.characters.character_profile import (
    CharacterProfile,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from backend.memory.memory_service import (
    MemoryService,
)


class CompanionService:
    """
    Coordinates AI companion experiences.

    The service orchestrates agents but does not contain
    provider-specific logic.
    """

    def __init__(
        self,
        character: CharacterProfile,
        conversation_agent=None,
        research_agent=None,
        quality_agent=None,
        memory_service=None,
    ):

        self.character = character

        self.conversation_agent = (
            conversation_agent
            or ConversationAgent(character)
        )

        self.research_agent = (
            research_agent
            or ResearchAgent()
        )

        self.quality_agent = (
            quality_agent
            or QualityAgent()
        )

        self.memory_service = (
            memory_service
            or MemoryService()
        )

    async def interact(
        self,
        context: ExecutionContext,
        use_research: bool = False,
    ):
        """
        Execute a complete companion interaction.

        When research is requested, the Research Agent
        produces an IntelligenceContext which is attached
        to a new immutable ExecutionContext before the
        Conversation Agent executes.

        The original ExecutionContext is never mutated.
        """

        memories = (
            self.memory_service.recall(
                context.user_id
            )
        )

        research_result = None

        conversation_context = context

        if use_research:

            research_result = (
                await self.research_agent.execute(
                    context
                )
            )

            if (
                research_result.success
                and research_result.output is not None
            ):
                conversation_context = replace(
                    context,
                    intelligence_context=(
                        research_result.output
                    ),
                )

        conversation_result = (
            await self.conversation_agent.execute(
                conversation_context
            )
        )

        quality_result = (
            await self.quality_agent.execute(
                conversation_context
            )
        )

        self.memory_service.remember(
            user_id=context.user_id,
            category="conversation",
            content=context.request,
        )

        return {
            "character": self.character.name,

            "conversation":
                conversation_result.output,

            "research":
                (
                    research_result.output
                    if research_result
                    else None
                ),

            "quality":
                quality_result.output,

            "memory_count":
                len(memories),
        }