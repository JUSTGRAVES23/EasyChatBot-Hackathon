"""
Companion Service.

Coordinates:

Character
Conversation Agent
Research Agent
Quality Agent
Memory Service

Application orchestration layer.
"""


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

        memories = (
            self.memory_service.recall(
                context.user_id
            )
        )


        research_result = None

        if use_research:

            research_result = (
                await self.research_agent.execute(
                    context
                )
            )


        conversation_result = (
            await self.conversation_agent.execute(
                context
            )
        )


        quality_result = (
            await self.quality_agent.execute(
                context
            )
        )


        self.memory_service.remember(
            user_id=context.user_id,
            category="conversation",
            content=context.request,
        )


        return {

            "character":
                self.character.name,


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