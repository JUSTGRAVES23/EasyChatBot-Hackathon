from __future__ import annotations

from .models import LearnerContext
from .repository import LearnerContextRepository


class LearnerContextService:
    """Builds the safe cross-channel learner-context read model.

    Responsibilities:
    - validate the authenticated learner/world request;
    - delegate context assembly to the existing persistence/integration layer;
    - enforce response-size limits;
    - return a canonical immutable application model.

    This service does not:
    - create Telegram bindings;
    - send Telegram invitations;
    - mutate Telegram history;
    - merge Telegram and Web conversation IDs;
    - erase learner data;
    - call an LLM.
    """

    DEFAULT_RECENT_LIMIT = 20
    MAX_RECENT_LIMIT = 20
    MAX_MEMORY_ITEMS = 50

    def __init__(
        self,
        *,
        repository: LearnerContextRepository,
    ) -> None:
        if repository is None:
            raise ValueError("repository is required.")

        self._repository = repository

    async def get(
        self,
        *,
        learner_id: str,
        world_id: str,
        recent_limit: int = DEFAULT_RECENT_LIMIT,
    ) -> LearnerContext:
        learner_id = self._validate_identifier(
            learner_id,
            field_name="learner_id",
        )
        world_id = self._validate_identifier(
            world_id,
            field_name="world_id",
        )

        if recent_limit < 1:
            raise ValueError("recent_limit must be greater than zero.")

        recent_limit = min(
            recent_limit,
            self.MAX_RECENT_LIMIT,
        )

        context = await self._repository.get(
            learner_id=learner_id,
            world_id=world_id,
            recent_limit=recent_limit,
        )

        if context is None:
            raise ValueError("Learner context not found.")

        if context.learner_id != learner_id:
            raise ValueError("Learner context ownership mismatch.")

        if context.world_id != world_id:
            raise ValueError("Learner context World mismatch.")

        if len(context.learning_memories) > self.MAX_MEMORY_ITEMS:
            context = LearnerContext(
                learner_id=context.learner_id,
                world_id=context.world_id,
                language_code=context.language_code,
                character=context.character,
                level=context.level,
                telegram_connected=context.telegram_connected,
                learning_memories=context.learning_memories[
                    : self.MAX_MEMORY_ITEMS
                ],
                recent_learning_context=context.recent_learning_context[
                    : self.MAX_RECENT_LIMIT
                ],
            )

        return context

    @staticmethod
    def _validate_identifier(
        value: str,
        *,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        value = value.strip()

        if not value:
            raise ValueError(f"{field_name} cannot be empty.")

        if len(value) > 128:
            raise ValueError(
                f"{field_name} is too long. Maximum length is 128 characters."
            )

        return value
