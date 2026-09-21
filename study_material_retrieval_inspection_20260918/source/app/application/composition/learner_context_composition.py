from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.application.conversation.conversation_event_repository import (
    ConversationEventRepository,
)
from app.application.learner_context.postgresql_repository import (
    CrossChannelLearnerContextRepository,
)
from app.application.learner_context.service import LearnerContextService
from app.application.memory.memory_repository import (
    ConversationMemoryRepository,
)
from app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)
from app.application.uai.world.world_resolver import WorldResolver
from app.infrastructure.persistence.postgresql_beta_access_repository import (
    PostgreSQLTelegramBindingRepository,
)
from app.infrastructure.persistence.postgresql_conversation_event_repository import (
    PostgreSQLConversationEventRepository,
)
from app.infrastructure.persistence.postgresql_memory_repository import (
    PostgreSQLConversationMemoryRepository,
)
from app.infrastructure.worlds.yaml_world_repository import YamlWorldRepository


def build_learner_context_service(
    *,
    telegram_bindings,
    memory_repository: ConversationMemoryRepository,
    conversation_event_repository: ConversationEventRepository,
    privacy_identifier_service: PrivacyIdentifierService,
    world_resolver: WorldResolver,
) -> LearnerContextService:
    """Compose the C4.2 cross-channel learner-context service.

    All dependencies are injected. This function creates no database
    connection and no persistence implementation.
    """
    repository = CrossChannelLearnerContextRepository(
        telegram_bindings=telegram_bindings,
        memory_repository=memory_repository,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        world_resolver=world_resolver,
    )

    return LearnerContextService(repository=repository)


def build_production_learner_context_service(
    *,
    session_factory: Any,
    world_resolver: WorldResolver | None = None,
    telegram_binding_repository=None,
    memory_repository: ConversationMemoryRepository | None = None,
    conversation_event_repository: ConversationEventRepository | None = None,
    privacy_identifier_service: PrivacyIdentifierService | None = None,
    world_repository_factory: Callable[[], Any] | None = None,
) -> LearnerContextService:
    """Build the production C4.2 service from existing infrastructure.

    The default path creates repositories against the supplied existing
    synchronous session factory. No new database engine is created here.

    Optional dependency arguments are exposed so application composition
    tests and future composition roots can inject already-created instances.
    """
    if session_factory is None:
        raise ValueError("session_factory is required.")

    if telegram_binding_repository is None:
        telegram_binding_repository = PostgreSQLTelegramBindingRepository(
            session_factory,
        )

    if memory_repository is None:
        memory_repository = PostgreSQLConversationMemoryRepository(
            session_factory,
        )

    if conversation_event_repository is None:
        conversation_event_repository = PostgreSQLConversationEventRepository(
            session_factory,
        )

    if privacy_identifier_service is None:
        privacy_identifier_service = PrivacyIdentifierService()

    if world_resolver is None:
        if world_repository_factory is not None:
            world_repository = world_repository_factory()
        else:
            app_root = Path(__file__).resolve().parents[2]
            world_repository = YamlWorldRepository(
                worlds_path=app_root / "configuration" / "worlds",
            )

        world_resolver = WorldResolver(
            world_repository=world_repository,
        )

    return build_learner_context_service(
        telegram_bindings=telegram_binding_repository,
        memory_repository=memory_repository,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        world_resolver=world_resolver,
    )


__all__ = [
    "build_learner_context_service",
    "build_production_learner_context_service",
]
