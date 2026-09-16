"""
Unit tests for CompanionService.

These tests verify the application orchestration boundary:

ExecutionContext
|
v
CompanionService
|
+--> MemoryService
|
+--> ResearchAgent
|       |
|       v
|   IntelligenceContext
|
+--> ConversationAgent
|
+--> QualityAgent
|
v
Interaction Result

No real LLM provider, OpenAI API, Parallel API,
or external infrastructure is called.
"""

from dataclasses import dataclass

import pytest

from agents.agent_result import (
    AgentResult,
)

from characters.character_profile import (
    CharacterProfile,
)

from runtime.context.execution_context import (
    ExecutionContext,
)

from services.companion_service import (
    CompanionService,
)


@dataclass
class FakeMemory:
    """
    Deterministic memory record for tests.
    """

    user_id: str
    category: str
    content: str


class FakeMemoryService:
    """
    Deterministic MemoryService test double.
    """

    def __init__(self) -> None:
        self.memories = [
            FakeMemory(
                user_id="demo-user",
                category="conversation",
                content="Previous conversation",
            ),
        ]

        self.recall_calls = []
        self.remember_calls = []

    def recall(
        self,
        user_id: str,
    ):
        self.recall_calls.append(
            user_id
        )

        return [
            memory
            for memory in self.memories
            if memory.user_id == user_id
        ]

    def remember(
        self,
        user_id: str,
        category: str,
        content: str,
    ) -> None:
        self.remember_calls.append(
            {
                "user_id": user_id,
                "category": category,
                "content": content,
            }
        )


class FakeResearchAgent:
    """
    Deterministic ResearchAgent test double.
    """

    def __init__(
        self,
        result: AgentResult,
    ) -> None:
        self.result = result
        self.received_contexts = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        self.received_contexts.append(
            context
        )

        return self.result


class FakeConversationAgent:
    """
    Deterministic ConversationAgent test double.
    """

    def __init__(
        self,
        result: AgentResult,
    ) -> None:
        self.result = result
        self.received_contexts = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        self.received_contexts.append(
            context
        )

        return self.result


class FakeQualityAgent:
    """
    Deterministic QualityAgent test double.
    """

    def __init__(
        self,
        result: AgentResult,
    ) -> None:
        self.result = result
        self.received_contexts = []

    async def execute(
        self,
        context: ExecutionContext,
    ) -> AgentResult:
        self.received_contexts.append(
            context
        )

        return self.result


def create_character() -> CharacterProfile:
    """
    Create a deterministic test character.
    """

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


def create_context(
    request: str = "Explain artificial intelligence",
) -> ExecutionContext:
    """
    Create a deterministic execution context.
    """

    return ExecutionContext(
        user_id="demo-user",
        request=request,
    )


@pytest.mark.asyncio
async def test_companion_service_orchestrates_conversation():
    """
    CompanionService should execute the ConversationAgent
    and QualityAgent for a normal interaction.

    Research must not execute when use_research=False.
    """

    conversation_agent = FakeConversationAgent(
        AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={
                "message": "Fake conversation response",
            },
        )
    )

    research_agent = FakeResearchAgent(
        AgentResult(
            success=True,
            agent_id="research_agent",
            output="Should not execute",
        )
    )

    quality_agent = FakeQualityAgent(
        AgentResult(
            success=True,
            agent_id="quality_agent",
            output={
                "quality_score": 1.0,
                "passed": True,
            },
        )
    )

    memory_service = FakeMemoryService()

    service = CompanionService(
        character=create_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=quality_agent,
        memory_service=memory_service,
    )

    context = create_context()

    result = await service.interact(
        context,
        use_research=False,
    )

    assert result["character"] == "Yeti"

    assert result["conversation"] == {
        "message": "Fake conversation response",
    }

    assert result["research"] is None

    assert result["quality"] == {
        "quality_score": 1.0,
        "passed": True,
    }

    assert result["memory_count"] == 1

    assert (
        len(
            conversation_agent.received_contexts
        )
        == 1
    )

    assert (
        conversation_agent.received_contexts[0]
        is context
    )

    assert (
        len(
            research_agent.received_contexts
        )
        == 0
    )

    assert (
        len(
            quality_agent.received_contexts
        )
        == 1
    )

    assert (
        quality_agent.received_contexts[0]
        is context
    )

    assert memory_service.recall_calls == [
        "demo-user",
    ]

    assert memory_service.remember_calls == [
        {
            "user_id": "demo-user",
            "category": "conversation",
            "content": (
                "Explain artificial intelligence"
            ),
        }
    ]


@pytest.mark.asyncio
async def test_companion_service_executes_research_when_requested():
    """
    When research is requested, CompanionService should:

    1. execute ResearchAgent
    2. attach its IntelligenceContext to a new
       ExecutionContext
    3. execute ConversationAgent with the enriched context
    4. execute QualityAgent with the enriched context
    """

    intelligence_context = object()

    research_agent = FakeResearchAgent(
        AgentResult(
            success=True,
            agent_id="research_agent",
            output=intelligence_context,
        )
    )

    conversation_agent = FakeConversationAgent(
        AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={
                "message": "Research-aware response",
            },
        )
    )

    quality_agent = FakeQualityAgent(
        AgentResult(
            success=True,
            agent_id="quality_agent",
            output={
                "quality_score": 0.95,
                "passed": True,
            },
        )
    )

    memory_service = FakeMemoryService()

    service = CompanionService(
        character=create_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=quality_agent,
        memory_service=memory_service,
    )

    context = create_context(
        "What are the latest AI developments?"
    )

    result = await service.interact(
        context,
        use_research=True,
    )

    assert result["character"] == "Yeti"

    assert result["conversation"] == {
        "message": "Research-aware response",
    }

    assert (
        result["research"]
        is intelligence_context
    )

    assert result["quality"] == {
        "quality_score": 0.95,
        "passed": True,
    }

    assert (
        len(
            research_agent.received_contexts
        )
        == 1
    )

    assert (
        research_agent.received_contexts[0]
        is context
    )

    assert (
        len(
            conversation_agent.received_contexts
        )
        == 1
    )

    enriched_context = (
        conversation_agent.received_contexts[0]
    )

    assert enriched_context is not context

    assert (
        enriched_context.request
        == context.request
    )

    assert (
        enriched_context.user_id
        == context.user_id
    )

    assert (
        enriched_context.intelligence_context
        is intelligence_context
    )

    assert (
        quality_agent.received_contexts[0]
        is enriched_context
    )


@pytest.mark.asyncio
async def test_companion_service_does_not_mutate_original_context():
    """
    Research enrichment must create a new
    ExecutionContext rather than mutating the original.
    """

    intelligence_context = object()

    research_agent = FakeResearchAgent(
        AgentResult(
            success=True,
            agent_id="research_agent",
            output=intelligence_context,
        )
    )

    conversation_agent = FakeConversationAgent(
        AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={
                "message": "Response",
            },
        )
    )

    quality_agent = FakeQualityAgent(
        AgentResult(
            success=True,
            agent_id="quality_agent",
            output={
                "quality_score": 1.0,
                "passed": True,
            },
        )
    )

    memory_service = FakeMemoryService()

    service = CompanionService(
        character=create_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=quality_agent,
        memory_service=memory_service,
    )

    context = create_context()

    assert (
        context.intelligence_context
        is None
    )

    await service.interact(
        context,
        use_research=True,
    )

    assert (
        context.intelligence_context
        is None
    )

    enriched_context = (
        conversation_agent.received_contexts[0]
    )

    assert enriched_context is not context

    assert (
        enriched_context.intelligence_context
        is intelligence_context
    )


@pytest.mark.asyncio
async def test_companion_service_handles_research_failure():
    """
    If research fails, ConversationAgent should still
    execute using the original context.

    The service should not attach failed research output
    to the conversation context.
    """

    research_agent = FakeResearchAgent(
        AgentResult(
            success=False,
            agent_id="research_agent",
            output=None,
        )
    )

    conversation_agent = FakeConversationAgent(
        AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={
                "message": "Fallback response",
            },
        )
    )

    quality_agent = FakeQualityAgent(
        AgentResult(
            success=True,
            agent_id="quality_agent",
            output={
                "quality_score": 0.9,
                "passed": True,
            },
        )
    )

    memory_service = FakeMemoryService()

    service = CompanionService(
        character=create_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=quality_agent,
        memory_service=memory_service,
    )

    context = create_context()

    result = await service.interact(
        context,
        use_research=True,
    )

    assert result["research"] is None

    assert result["conversation"] == {
        "message": "Fallback response",
    }

    assert (
        conversation_agent.received_contexts[0]
        is context
    )

    assert (
        conversation_agent.received_contexts[0]
        .intelligence_context
        is None
    )


def test_companion_service_uses_injected_dependencies():
    """
    CompanionService should preserve explicitly injected
    dependencies rather than replacing them with defaults.
    """

    conversation_agent = FakeConversationAgent(
        AgentResult(
            success=True,
            agent_id="conversation_agent",
            output={},
        )
    )

    research_agent = FakeResearchAgent(
        AgentResult(
            success=True,
            agent_id="research_agent",
            output=None,
        )
    )

    quality_agent = FakeQualityAgent(
        AgentResult(
            success=True,
            agent_id="quality_agent",
            output={},
        )
    )

    memory_service = FakeMemoryService()

    service = CompanionService(
        character=create_character(),
        conversation_agent=conversation_agent,
        research_agent=research_agent,
        quality_agent=quality_agent,
        memory_service=memory_service,
    )

    assert (
        service.conversation_agent
        is conversation_agent
    )

    assert (
        service.research_agent
        is research_agent
    )

    assert (
        service.quality_agent
        is quality_agent
    )

    assert (
        service.memory_service
        is memory_service
    )
