"""
Challenge Engine Data Models.

Defines the provider-independent contracts used by the
Challenge Generation layer.

Architecture:

Live Intelligence Agent
        |
        v
Challenge Engine Models
        |
        v
Challenge Generator
        |
        v
Learning Challenge Output

Responsibilities:
- Define structured learning challenge data
- Keep challenge generation independent from providers/models
- Provide stable contracts for application layers

Non-responsibilities:
- LLM calls
- Search operations
- Agent execution
- User interface handling
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class VocabularyItem:
    """
    Vocabulary item generated from learning content.
    """

    term: str
    definition: str
    example: str | None = None


@dataclass(frozen=True)
class DiscussionQuestion:
    """
    Conversation practice question.
    """

    question: str
    difficulty: str = "B2"


@dataclass(frozen=True)
class LearningChallenge:
    """
    Complete learning challenge output.

    This is the main contract returned
    by the Challenge Engine.
    """

    title: str
    topic: str
    language: str
    learner_level: str

    summary: str

    vocabulary: List[VocabularyItem]

    discussion_questions: List[DiscussionQuestion]

    created_by_agent: str = "live_intelligence_agent"