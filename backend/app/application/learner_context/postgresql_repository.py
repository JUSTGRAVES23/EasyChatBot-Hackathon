from __future__ import annotations

from app.application.beta_access.repositories import (
    TelegramBindingRepository,
)
from app.application.memory.memory_repository import (
    ConversationMemoryRepository,
)
from app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)
from app.application.conversation.conversation_event_repository import (
    ConversationEventRepository,
)
from app.application.uai.world.world_resolver import WorldResolver

from .models import LearnerContext
from .repository import LearnerContextRepository
from .telegram_projection import TelegramLearningContextProjector


class CrossChannelLearnerContextRepository(LearnerContextRepository):
    """Concrete C4.2/C4.3 repository composed from existing application ports.

    No Telegram, memory or conversation tables are introduced here. The
    repository translates the existing Telegram-scoped stores into the
    canonical learner/world read model created by C4.1.

    World compatibility
    -------------------
    Existing Beta/Telegram data may contain legacy World identifiers such as
    ``world-fr`` while the runtime World configuration uses the canonical
    identifier ``french_world``.

    The requested World identifier is always attempted first. A legacy alias
    is used only when the requested identifier cannot be resolved.

    The original requested identifier remains the storage scope for Telegram
    memories and conversation events. Runtime World resolution is therefore
    compatible with the current YAML World configuration without modifying
    historical production data.
    """

    CHARACTER = "Alix"
    LEVEL = "B1"

    # Existing Beta/Telegram compatibility identifiers.
    #
    # These mappings are intentionally local to this compatibility boundary.
    # They do not alter persistence identifiers.
    LEGACY_WORLD_ALIASES = {
        "world-fr": "french_world",
    }

    def __init__(
        self,
        *,
        telegram_bindings: TelegramBindingRepository,
        memory_repository: ConversationMemoryRepository,
        conversation_event_repository: ConversationEventRepository,
        privacy_identifier_service: PrivacyIdentifierService,
        world_resolver: WorldResolver,
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

        if world_resolver is None:
            raise ValueError("world_resolver is required.")

        self._world_resolver = world_resolver

        self._telegram_projector = TelegramLearningContextProjector(
            telegram_bindings=telegram_bindings,
            memory_repository=memory_repository,
            conversation_event_repository=conversation_event_repository,
            privacy_identifier_service=privacy_identifier_service,
        )

    async def get(
        self,
        *,
        learner_id: str,
        world_id: str,
        recent_limit: int,
    ) -> LearnerContext | None:
        """Assemble context for one authenticated learner and World.

        The requested World identifier is preserved as the cross-channel
        storage scope.

        Runtime resolution first attempts the requested identifier. If that
        identifier is a known legacy alias and cannot be resolved, the
        canonical runtime identifier is attempted.

        This allows historical Telegram data using ``world-fr`` to remain
        readable while the active runtime World is ``french_world``.
        """

        world = self._resolve_world(world_id)

        projection = await self._telegram_projector.project(
            learner_id=learner_id,
            world_id=world_id,
            recent_limit=recent_limit,
        )

        return LearnerContext(
            learner_id=learner_id,
            world_id=world_id,
            language_code=world.language_code or "",
            character=self.CHARACTER,
            level=self.LEVEL,
            telegram_connected=projection.telegram_connected,
            learning_memories=projection.learning_memories,
            recent_learning_context=projection.recent_learning_context,
        )

    def _resolve_world(self, world_id: str):
        """Resolve a requested World with legacy compatibility fallback.

        The requested identifier is authoritative when it exists.

        For a known legacy identifier, the canonical runtime identifier is
        attempted only after the original identifier fails to resolve.

        Unknown identifiers fail through the existing WorldResolver contract.
        """

        try:
            world = self._world_resolver.resolve(world_id)
        except ValueError as exc:
            canonical_world_id = self.LEGACY_WORLD_ALIASES.get(
                world_id
            )

            if canonical_world_id is None:
                raise

            world = self._world_resolver.resolve(
                canonical_world_id
            )

        if world.world_id not in {
            world_id,
            self.LEGACY_WORLD_ALIASES.get(world_id),
        }:
            raise ValueError(
                "Resolved World mismatch."
            )

        return world


__all__ = [
    "CrossChannelLearnerContextRepository",
]