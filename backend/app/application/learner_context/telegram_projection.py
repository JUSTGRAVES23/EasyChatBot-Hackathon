from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import LearnerContextMessage, LearnerContextMemory


class TelegramBindingReader(Protocol):
    async def get_by_user_id(self, user_id: str): ...


class LearningMemoryReader(Protocol):
    async def get_user_memories(
        self,
        *,
        telegram_user_id: str,
        world_id: str,
    ): ...


class ConversationEventReader(Protocol):
    async def get_recent(
        self,
        *,
        telegram_user_hash: str,
        conversation_id: str,
        world_id: str,
        limit: int = 20,
    ): ...


class PrivacyIdentifier(Protocol):
    def pseudonymize_identifier(self, value: str) -> str: ...


@dataclass(frozen=True, slots=True)
class TelegramLearningProjection:
    """Safe Telegram-derived learning projection.

    Raw Telegram identity is deliberately kept private to this adapter. The
    application-facing values contain only learning memories and a bounded
    role/content projection of recent Telegram learning activity.
    """

    telegram_connected: bool
    learning_memories: tuple[LearnerContextMemory, ...]
    recent_learning_context: tuple[LearnerContextMessage, ...]


class TelegramLearningContextProjector:
    """Projects existing Telegram learning data into C4.1's safe model.

    This class is intentionally an adapter, not a new persistence layer.
    It reuses the existing Telegram binding, memory repository, event
    repository and privacy pseudonymisation contract.
    """

    TELEGRAM_CONVERSATION_PREFIX = "telegram-"
    MAX_MEMORY_ITEMS = 50

    def __init__(
        self,
        *,
        telegram_bindings: TelegramBindingReader,
        memory_repository: LearningMemoryReader,
        conversation_event_repository: ConversationEventReader,
        privacy_identifier_service: PrivacyIdentifier,
    ) -> None:
        if telegram_bindings is None:
            raise ValueError("telegram_bindings is required.")
        if memory_repository is None:
            raise ValueError("memory_repository is required.")
        if conversation_event_repository is None:
            raise ValueError(
                "conversation_event_repository is required."
            )
        if privacy_identifier_service is None:
            raise ValueError(
                "privacy_identifier_service is required."
            )

        self._telegram_bindings = telegram_bindings
        self._memory_repository = memory_repository
        self._events = conversation_event_repository
        self._privacy = privacy_identifier_service

    async def project(
        self,
        *,
        learner_id: str,
        world_id: str,
        recent_limit: int,
    ) -> TelegramLearningProjection:
        binding = await self._telegram_bindings.get_by_user_id(learner_id)

        if binding is None:
            return TelegramLearningProjection(
                telegram_connected=False,
                learning_memories=(),
                recent_learning_context=(),
            )

        telegram_user_id = str(binding.telegram_user_id)

        memories = await self._memory_repository.get_user_memories(
            telegram_user_id=telegram_user_id,
            world_id=world_id,
        )

        telegram_user_hash = self._privacy.pseudonymize_identifier(
            telegram_user_id
        )
        conversation_id = (
            f"{self.TELEGRAM_CONVERSATION_PREFIX}"
            f"{telegram_user_hash[:16]}"
        )

        events = await self._events.get_recent(
            telegram_user_hash=telegram_user_hash,
            conversation_id=conversation_id,
            world_id=world_id,
            limit=recent_limit,
        )

        projected_memories = tuple(
            LearnerContextMemory(
                memory_type=str(memory.memory_key),
                content=str(memory.memory_value),
            )
            for memory in memories[: self.MAX_MEMORY_ITEMS]
            if memory.memory_key and memory.memory_value
        )

        projected_events = tuple(
            LearnerContextMessage(
                role=str(event.role),
                content=str(event.content),
            )
            for event in events
            if event.role and event.content
        )

        return TelegramLearningProjection(
            telegram_connected=True,
            learning_memories=projected_memories,
            recent_learning_context=projected_events,
        )
