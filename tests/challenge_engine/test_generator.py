"""
Tests for Challenge Generator.
"""

import pytest

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceResponse,
)

from src.challenge_engine.generator import (
    ChallengeGenerator,
)

from src.challenge_engine.models import (
    DiscussionQuestion,
    VocabularyItem,
)


class FakeContentGenerator:

    async def generate_vocabulary(
        self,
        summary,
        language,
        learner_level,
    ):
        return [
            VocabularyItem(
                term="innovation",
                definition="A new idea or approach.",
            )
        ]

    async def generate_questions(
        self,
        summary,
        language,
        learner_level,
    ):
        return [
            DiscussionQuestion(
                question="Quel est votre avis ?"
            )
        ]


@pytest.mark.asyncio
async def test_generate_learning_challenge():

    generator = ChallengeGenerator(
        content_generator=FakeContentGenerator()
    )

    intelligence = LiveIntelligenceResponse(
        topic="AI Regulation",
        summary="AI regulation is evolving.",
        sources=[],
        key_information=[
            "governance"
        ],
    )

    result = await generator.generate(
        intelligence
    )

    assert result.topic == "AI Regulation"
    assert result.language == "French"
    assert result.vocabulary[0].term == "innovation"
    assert len(result.discussion_questions) == 1


@pytest.mark.asyncio
async def test_generator_rejects_empty_summary():

    generator = ChallengeGenerator(
        content_generator=FakeContentGenerator()
    )

    intelligence = LiveIntelligenceResponse(
        topic="AI",
        summary="",
        sources=[],
        key_information=[],
    )

    with pytest.raises(ValueError):
        await generator.generate(
            intelligence
        )