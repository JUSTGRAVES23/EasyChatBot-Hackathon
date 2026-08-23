from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class LearningPortfolio:
    """
    Learner academic progress representation.
    """

    learner_hash: str
    completed_lessons: list[str] = field(default_factory=list)
    vocabulary_progress: list[str] = field(default_factory=list)
    grammar_progress: list[str] = field(default_factory=list)
    pronunciation_milestones: list[str] = field(default_factory=list)
