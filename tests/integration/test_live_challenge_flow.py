"""
Integration test for Live Challenge vertical slice.

Flow tested:

Search Provider
        ↓
Live Intelligence Agent
        ↓
Challenge Generator
        ↓
Learning Challenge

This test validates the Sprint H1 integration boundaries.

Important:
- Uses test doubles only.
- Does not call the real Parallel API.
- Does not modify or depend on the Conversation Agent.
"""

import pytest

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceAgent,
    LiveIntelligenceRequest,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.models import (
    DiscussionQuestion,
    VocabularyItem,
)

from src.providers.search_provider.interface import (
    SearchResult,
)


class FakeSearchProvider:
    """
    Controlled search provider for integration testing.
    """

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                title="AI Act Update",
                url="https://example.com/ai-act",
                content="European AI regulation update.",
                source="test-provider",
            )
        ]


class FakeIntelligenceProcessor:
    """
    Simulates intelligence synthesis without
    requiring an LLM provider.
    """

    async def summarise(
        self,
        results: list[SearchResult],
        language: str,
        learner_level: str,
    ) -> tuple[str, list[str]]:
        return (
            "The AI Act introduces new rules for "
            "artificial intelligence.",
            [
                "AI governance",
                "risk management",
            ],
        )


class FakeChallengeContentGenerator:
    """
    Simulates educational content generation.
    """

    async def generate_vocabulary(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[VocabularyItem]:
        return [
            VocabularyItem(
                term="gouvernance",
                definition=(
                    "Organisation and control of activities."
                ),
            )
        ]

    async def generate_questions(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> list[DiscussionQuestion]:
        return [
            DiscussionQuestion(
                question=(
                    "Pourquoi la gouvernance de l'IA "
                    "est-elle importante ?"
                ),
            )
        ]


@pytest.mark.asyncio
async def test_live_challenge_vertical_slice():
    """
    Validate the complete Sprint H1 backend flow:

    Search Provider
        ↓
    Live Intelligence Agent
        ↓
    Challenge Generator
        ↓
    Learning Challenge
    """

    # ---------------------------------------------------------
    # Step 1 — Create Live Intelligence Agent
    # ---------------------------------------------------------

    intelligence_agent = LiveIntelligenceAgent(
        search_provider=FakeSearchProvider(),
        processor=FakeIntelligenceProcessor(),
    )

    # ---------------------------------------------------------
    # Step 2 — Execute Live Intelligence research
    # ---------------------------------------------------------

    intelligence = await intelligence_agent.execute(
        request=LiveIntelligenceRequest(
            topic="AI Act",
        )
    )

    # ---------------------------------------------------------
    # Step 3 — Validate intelligence output
    # ---------------------------------------------------------

    assert intelligence.topic == "AI Act"

    assert intelligence.summary == (
        "The AI Act introduces new rules for "
        "artificial intelligence."
    )

    assert intelligence.key_information == [
        "AI governance",
        "risk management",
    ]

    assert len(intelligence.sources) == 1
    assert intelligence.sources[0].title == "AI Act Update"
    assert intelligence.sources[0].source == "test-provider"

    # ---------------------------------------------------------
    # Step 4 — Create Challenge Generator
    # ---------------------------------------------------------

    challenge_generator = ChallengeGenerator(
        content_generator=FakeChallengeContentGenerator()
    )

    # ---------------------------------------------------------
    # Step 5 — Generate learning challenge
    # ---------------------------------------------------------

    challenge = await challenge_generator.generate(
        intelligence=intelligence,
        language="French",
        learner_level="B2",
    )

    # ---------------------------------------------------------
    # Step 6 — Validate final learning output
    # ---------------------------------------------------------

    assert challenge.title == (
        "AI Act Learning Challenge"
    )

    assert challenge.topic == "AI Act"
    assert challenge.language == "French"
    assert challenge.learner_level == "B2"

    assert challenge.summary == (
        "The AI Act introduces new rules for "
        "artificial intelligence."
    )

    assert len(challenge.vocabulary) == 1

    assert challenge.vocabulary[0].term == (
        "gouvernance"
    )

    assert (
        challenge.vocabulary[0].definition
        == "Organisation and control of activities."
    )

    assert len(challenge.discussion_questions) == 1

    assert (
        challenge.discussion_questions[0].question
        == "Pourquoi la gouvernance de l'IA est-elle importante ?"
    )

    assert (
        challenge.discussion_questions[0].difficulty
        == "B2"
    )

    assert (
        challenge.created_by_agent
        == "live_intelligence_agent"
    )