"""
Companion Service.

Application orchestration layer for EasyChatBot.

Coordinates:

Character
Conversation Agent
Research Agent
Quality Agent
Memory Service
Memory Context Builder

Live Intelligence + Memory flow:

CompanionService
|
+--> MemoryService
|        |
|        v
|   MemoryRecord[]
|        |
|        v
|   MemoryContextBuilder
|        |
|        v
|   MemoryContext
|
+--> ResearchAgent
|        |
|        v
|   IntelligenceContext
|
+--> ConversationAgent
|        |
|        v
|   LLMService
|        |
|        v
|   LLMProvider
|
+--> QualityAgent
|
v
Interaction Result

Responsibilities:

- orchestrate companion interactions
- retrieve memories
- build bounded learner memory context
- optionally execute research
- enrich the execution context with memory
- enrich the execution context with live intelligence
- execute the ConversationAgent
- execute the QualityAgent
- persist the interaction
- return the combined result

Does not:

- create LLM providers
- select LLM providers
- call provider SDKs
- call OpenAI directly
- call Ollama directly
- manage provider routing
- build provider-specific prompts
- persist memory directly
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

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

from backend.memory.memory_service import (
    MemoryService,
)

from backend.runtime.context.execution_context import (
    ExecutionContext,
)

from src.ai_runtime.memory.context_builder import (
    MemoryContextBuilder,
)


class CompanionService:
    """
    Coordinates AI companion experiences.

    The service orchestrates agents but does not contain
    provider-specific logic.

    Providers are injected into agents by the composition
    layer.

    Memory retrieval remains owned by MemoryService.

    MemoryContextBuilder converts already-retrieved memory
    into bounded runtime context.

    ExecutionContext remains immutable. Enrichment is
    performed using dataclasses.replace().
    """

    def __init__(
        self,
        character: CharacterProfile,
        conversation_agent: ConversationAgent | None = None,
        research_agent: ResearchAgent | None = None,
        quality_agent: QualityAgent | None = None,
        memory_service: MemoryService | None = None,
        memory_context_builder: (MemoryContextBuilder | None) = None,
    ) -> None:
        """
        Initialise the CompanionService.

        Dependencies are injectable so the service can be
        tested without invoking real infrastructure.
        """

        self.character = character

        self.conversation_agent = (
            conversation_agent
            if conversation_agent is not None
            else ConversationAgent(character)
        )

        self.research_agent = (
            research_agent if research_agent is not None else ResearchAgent()
        )

        self.quality_agent = (
            quality_agent if quality_agent is not None else QualityAgent()
        )

        self.memory_service = (
            memory_service if memory_service is not None else MemoryService()
        )

        self.memory_context_builder = (
            memory_context_builder
            if memory_context_builder is not None
            else MemoryContextBuilder()
        )

    async def interact(
        self,
        context: ExecutionContext,
        use_research: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a complete companion interaction.

        Flow:

        MemoryService
            ↓
        MemoryContextBuilder
            ↓
        optional memory-enriched ExecutionContext
            ↓
        optional ResearchAgent
            ↓
        optional intelligence-enriched ExecutionContext
            ↓
        ConversationAgent
            ↓
        QualityAgent
            ↓
        MemoryService.remember()

        The original ExecutionContext is never mutated.

        Parameters
        ----------
        context:
            Runtime execution context.

        use_research:
            Whether live research should be performed
            before the conversation response.

        Returns
        -------
        dict[str, Any]
            Combined companion interaction result.

        Raises
        ------
        ValueError
            If the execution context is missing.
        """

        if context is None:
            raise ValueError("Execution context cannot be None.")

        # -----------------------------------------------------
        # Step 1 — Retrieve existing learner memory
        # -----------------------------------------------------

        memories = self.memory_service.recall(context.user_id)

        # -----------------------------------------------------
        # Step 2 — Build bounded learner memory context
        # -----------------------------------------------------

        memory_context = self.memory_context_builder.build(
            user_id=context.user_id,
            request=context.request,
            memories=memories,
        )

        # -----------------------------------------------------
        # Step 3 — Attach memory only when relevant memory
        # exists.
        #
        # If there is no relevant memory, preserve the
        # original ExecutionContext object.
        # -----------------------------------------------------

        if memory_context.is_empty:
            conversation_context = context
        else:
            conversation_context = replace(
                context,
                memory_context=memory_context,
            )

        # -----------------------------------------------------
        # Step 4 — Optional Live Intelligence
        #
        # Research receives the current runtime context but
        # does not receive or manage memory itself.
        #
        # If research succeeds, create another immutable
        # context preserving the existing memory_context.
        # -----------------------------------------------------

        research_result = None

        if use_research:
            research_result = await self.research_agent.execute(conversation_context)

            if research_result.success and research_result.output is not None:
                conversation_context = replace(
                    conversation_context,
                    intelligence_context=(research_result.output),
                )

        # -----------------------------------------------------
        # Step 5 — Conversation Agent
        #
        # ConversationAgent can now receive:
        #
        #   memory_context
        #   intelligence_context
        #
        # independently or together.
        # -----------------------------------------------------

        conversation_result = await self.conversation_agent.execute(
            conversation_context
        )

        # -----------------------------------------------------
        # Step 6 — Quality Agent
        # -----------------------------------------------------

        quality_result = await self.quality_agent.execute(conversation_context)

        # -----------------------------------------------------
        # Step 7 — Persist interaction
        #
        # Memory persistence remains owned by MemoryService.
        # -----------------------------------------------------

        self.memory_service.remember(
            user_id=context.user_id,
            category="conversation",
            content=context.request,
        )

        # -----------------------------------------------------
        # Step 8 — Return combined result
        # -----------------------------------------------------

        return {
            "character": self.character.name,
            "conversation": (conversation_result.output),
            "research": (
                research_result.output
                if (research_result is not None and research_result.success)
                else None
            ),
            "quality": (quality_result.output),
            "memory_count": len(memories),
            "memory_context_count": (memory_context.memory_count),
        }
