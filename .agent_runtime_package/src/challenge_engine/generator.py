"""
Challenge Engine Generator.

Transforms structured intelligence output into
a learner-facing challenge.

Architecture:

Live Intelligence Agent
        |
        v
Challenge Generator
        |
        v
LearningChallenge

Responsibilities:
- Convert research intelligence into learning structure
- Apply learner level/language context
- Produce deterministic challenge objects

Non-responsibilities:
- Search
- Provider calls
- Agent orchestration
- Direct LLM dependency

Future extension:
- Inject LLM-based content generation service
- Add templates/configuration-driven challenges
"""

from typing import Protocol, List

from src.ai_agents.live_intelligence_agent.handler import (
    LiveIntelligenceResponse,
)

from src.challenge_engine.models import (
    DiscussionQuestion,
    LearningChallenge,
    VocabularyItem,
)


class ChallengeContentGenerator(Protocol):
    """
    Contract for optional AI-powered content generation.

    Keeps Challenge Engine independent from
    a specific LLM provider.
    """

    async def generate_vocabulary(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> List[VocabularyItem]:
        ...

    async def generate_questions(
        self,
        summary: str,
        language: str,
        learner_level: str,
    ) -> List[DiscussionQuestion]:
        ...


class ChallengeGenerator:
    """
    Generates learning challenges from intelligence output.
    """

    def __init__(
        self,
        content_generator: ChallengeContentGenerator,
    ) -> None:
        self._content_generator = content_generator

    async def generate(
        self,
        intelligence: LiveIntelligenceResponse,
        language: str = "French",
        learner_level: str = "B2",
    ) -> LearningChallenge:
        """
        Transform intelligence into learning challenge.

        Flow:

        Research Output
              |
              v
        Vocabulary Generation
              |
              v
        Discussion Generation
              |
              v
        Learning Challenge
        """

        if not intelligence.summary.strip():
            raise ValueError(
                "Intelligence summary cannot be empty"
            )

        vocabulary = await self._content_generator.generate_vocabulary(
            summary=intelligence.summary,
            language=language,
            learner_level=learner_level,
        )

        questions = await self._content_generator.generate_questions(
            summary=intelligence.summary,
            language=language,
            learner_level=learner_level,
        )

        return LearningChallenge(
            title=f"{intelligence.topic} Learning Challenge",
            topic=intelligence.topic,
            language=language,
            learner_level=learner_level,
            summary=intelligence.summary,
            vocabulary=vocabulary,
            discussion_questions=questions,
        )