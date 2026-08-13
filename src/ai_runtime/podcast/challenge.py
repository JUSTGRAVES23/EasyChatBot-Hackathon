"""
EasyChatBot Hackathon — Podcast Learning Challenge contracts.

Presentation/learning contract only. This module does not download audio,
transcribe podcasts, call providers, or execute external actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class VocabularyItem:
    """A vocabulary item presented to the learner."""

    term: str
    meaning: str
    example: str

    def __post_init__(self) -> None:
        for name, value in {
            "term": self.term,
            "meaning": self.meaning,
            "example": self.example,
        }.items():
            if not value.strip():
                raise ValueError(
                    f"VocabularyItem {name} cannot be empty."
                )


@dataclass(frozen=True)
class ComprehensionQuestion:
    """A multiple-choice comprehension question."""

    question: str
    options: tuple[str, ...]
    correct_option: int

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError(
                "ComprehensionQuestion question cannot be empty."
            )

        if len(self.options) < 2:
            raise ValueError(
                "ComprehensionQuestion requires at least two options."
            )

        if any(not option.strip() for option in self.options):
            raise ValueError(
                "ComprehensionQuestion options cannot be empty."
            )

        if not 0 <= self.correct_option < len(self.options):
            raise ValueError(
                "ComprehensionQuestion correct_option is out of range."
            )


@dataclass(frozen=True)
class PodcastLearningChallenge:
    """Learner-facing challenge derived from a verified podcast recommendation."""

    challenge_id: str
    user_id: str
    podcast_id: str
    podcast_title: str
    podcast_url: str
    target_language: str
    learner_level: str
    vocabulary: tuple[VocabularyItem, ...]
    comprehension_questions: tuple[ComprehensionQuestion, ...]
    discussion_prompt: str
    introduction: str
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "podcast_id": self.podcast_id,
            "podcast_title": self.podcast_title,
            "podcast_url": self.podcast_url,
            "target_language": self.target_language,
            "learner_level": self.learner_level,
            "discussion_prompt": self.discussion_prompt,
            "introduction": self.introduction,
        }

        for name, value in required.items():
            if not value.strip():
                raise ValueError(
                    f"PodcastLearningChallenge {name} cannot be empty."
                )

        if not (
            self.podcast_url.startswith("https://")
            or self.podcast_url.startswith("http://")
        ):
            raise ValueError(
                "PodcastLearningChallenge podcast_url must use HTTP or HTTPS."
            )

        if not self.vocabulary:
            raise ValueError(
                "PodcastLearningChallenge requires vocabulary."
            )

        if not self.comprehension_questions:
            raise ValueError(
                "PodcastLearningChallenge requires comprehension questions."
            )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        podcast_id: str,
        podcast_title: str,
        podcast_url: str,
        target_language: str,
        learner_level: str,
        vocabulary: tuple[VocabularyItem, ...],
        comprehension_questions: tuple[ComprehensionQuestion, ...],
        discussion_prompt: str,
        introduction: str,
        metadata: dict[str, str] | None = None,
    ) -> "PodcastLearningChallenge":
        return cls(
            challenge_id=str(uuid4()),
            user_id=user_id,
            podcast_id=podcast_id,
            podcast_title=podcast_title,
            podcast_url=podcast_url,
            target_language=target_language,
            learner_level=learner_level,
            vocabulary=vocabulary,
            comprehension_questions=comprehension_questions,
            discussion_prompt=discussion_prompt,
            introduction=introduction,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class ChallengeResult:
    """Result of a learner completing the comprehension part."""

    challenge_id: str
    user_id: str
    score: int
    total_questions: int
    passed: bool
    vocabulary_review_required: bool
    message: str

    def __post_init__(self) -> None:
        if self.total_questions < 1:
            raise ValueError(
                "ChallengeResult total_questions must be at least 1."
            )

        if not 0 <= self.score <= self.total_questions:
            raise ValueError(
                "ChallengeResult score must be between 0 and total_questions."
            )

        if not self.message.strip():
            raise ValueError(
                "ChallengeResult message cannot be empty."
            )
