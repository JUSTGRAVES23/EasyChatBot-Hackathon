import pytest

from agents.agent_result import (
    AgentResult,
)

from characters.character_profile import (
    CharacterProfile,
)

from intelligence.intelligence_context import (
    IntelligenceContext,
    IntelligenceSource,
)

from memory.memory_service import (
    MemoryService,
)

from memory.memory_store import (
    MemoryStore,
)

from runtime.context.execution_context import (
    ExecutionContext,
)

from services.companion_service import (
    CompanionService,
)


class FakeConversationAgent:

    def __init__(self):
        self.received_context = None

    async def execute(
        self,
        context,
    ):
        self.received_context = context

        return AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={
                "character": "Yeti",
                "personality": (
                    "Curious and encouraging"
                ),
                "learning_style": (
                    "Conversation based learning"
                ),
                "intelligence_context": (
                    context.intelligence_context
                ),
            },
        )


class FakeResearchAgent:

    async def execute(
        self,
        context,
    ):
        return AgentResult(
            success=True,
            agent_id="research_agent",
            output=IntelligenceContext(
                query=context.request,
                sources=(
                    IntelligenceSource(
                        title=(
                            "European AI Regulation"
                        ),
                        url=(
                            "https://example.com/ai"
                        ),
                        source="test",
                        content=(
                            "Current regulatory "
                            "information."
                        ),
                    ),
                ),
                summary=(
                    "Recent European AI "
                    "regulatory developments."
                ),
            ),
        )


class FakeQualityAgent:

    async def execute(
        self,
        context,
    ):
        return AgentResult(
            success=True,
            agent_id="quality_agent",
            output={
                "quality_score": 1.0,
                "passed": True,
                "findings": [],
                "recommendations": [],
            },
        )


def create_character():
    return CharacterProfile(
        character_id="yeti",
        name="Yeti",
        description=(
            "Friendly AI learning companion"
        ),
        personality=(
            "Curious and encouraging"
        ),
        learning_style=(
            "Conversation based learning"
        ),
    )


def create_memory_service(
    tmp_path,
):
    return MemoryService(
        store=MemoryStore(
            database_path=(
                tmp_path / "memory.db"
            )
        )
    )


@pytest.mark.asyncio
async def test_companion_passes_research_to_conversation(
    tmp_path,
):

    conversation_agent = (
        FakeConversationAgent()
    )

    service = CompanionService(
        character=create_character(),
        conversation_agent=(
            conversation_agent
        ),
        research_agent=(
            FakeResearchAgent()
        ),
        quality_agent=(
            FakeQualityAgent()
        ),
        memory_service=(
            create_memory_service(
                tmp_path
            )
        ),
    )

    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "Explain the latest "
            "European AI regulation"
        ),
    )

    result = await service.interact(
        context,
        use_research=True,
    )

    assert result["character"] == (
        "Yeti"
    )

    assert (
        result["research"]
        is not None
    )

    assert isinstance(
        result["research"],
        IntelligenceContext,
    )

    received_context = (
        conversation_agent.received_context
    )

    assert (
        received_context is not None
    )

    assert (
        received_context
        is not context
    )

    assert (
        received_context.intelligence_context
        is not None
    )

    assert (
        received_context.intelligence_context.query
        == context.request
    )

    assert (
        received_context.intelligence_context.source_count
        == 1
    )

    assert (
        result["conversation"][
            "intelligence_context"
        ]
        is received_context.intelligence_context
    )

    assert (
        context.intelligence_context
        is None
    )


@pytest.mark.asyncio
async def test_companion_without_research_preserves_normal_conversation(
    tmp_path,
):

    conversation_agent = (
        FakeConversationAgent()
    )

    service = CompanionService(
        character=create_character(),
        conversation_agent=(
            conversation_agent
        ),
        research_agent=(
            FakeResearchAgent()
        ),
        quality_agent=(
            FakeQualityAgent()
        ),
        memory_service=(
            create_memory_service(
                tmp_path
            )
        ),
    )

    context = ExecutionContext(
        user_id="demo-user",
        request=(
            "Explain artificial intelligence"
        ),
    )

    result = await service.interact(
        context,
        use_research=False,
    )

    assert result["research"] is None

    assert (
        conversation_agent.received_context
        is context
    )

    assert (
        conversation_agent.received_context
        .intelligence_context
        is None
    )

    assert (
        result["conversation"][
            "intelligence_context"
        ]
        is None
    )
