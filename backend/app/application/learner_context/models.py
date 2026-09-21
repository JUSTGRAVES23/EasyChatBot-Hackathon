from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LearnerContextMemory:
    """Governance-approved learning memory safe for application consumption."""

    memory_type: str
    content: str


@dataclass(frozen=True, slots=True)
class LearnerContextMessage:
    """Small learning-context projection of prior cross-channel activity.

    This is intentionally not a persistence/event model. Database identifiers,
    Telegram identifiers, privacy hashes and governance metadata are excluded.
    """

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LearnerContext:
    """Canonical cross-channel learner context for one World.

    `learner_id` is the authenticated EasyChatBot user identity. No raw
    Telegram identity is included in this model.
    """

    learner_id: str
    world_id: str
    language_code: str
    character: str
    level: str
    telegram_connected: bool
    learning_memories: tuple[LearnerContextMemory, ...]
    recent_learning_context: tuple[LearnerContextMessage, ...]
