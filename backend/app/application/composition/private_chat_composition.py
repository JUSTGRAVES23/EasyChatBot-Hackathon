from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.ai_runtime.conversation.conversation_runtime import ConversationRuntime
from app.application.private_chat.service import PrivateChatService
from app.application.services.world_access_service import WorldAccessService
from app.application.uai.language.language_detector import LanguageDetector
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.application.uai.world.world_resolver import WorldResolver
from app.infrastructure.persistence.postgresql_private_chat_repository import (
    PostgreSQLPrivateChatRepository,
)
from app.infrastructure.worlds.yaml_world_repository import YamlWorldRepository


def build_private_chat_service_factory(
    *,
    session_factory: sessionmaker[Session],
    conversation_runtime: ConversationRuntime,
    character_instruction: str,
    world_access_service: WorldAccessService,
    language_detector: LanguageDetector | None = None,
) -> Callable[[], PrivateChatService]:
    """Build a request-scoped private-chat service factory.

    Every invocation creates exactly one SQLAlchemy Session. The returned
    service closes that session through its repository when the HTTP request
    finishes. No database session is shared between requests.
    """

    if session_factory is None:
        raise ValueError("session_factory is required.")
    if conversation_runtime is None:
        raise ValueError("conversation_runtime is required.")
    if not character_instruction or not character_instruction.strip():
        raise ValueError("character_instruction is required.")
    if world_access_service is None:
        raise ValueError("world_access_service is required.")

    app_root = Path(__file__).resolve().parents[2]
    world_repository = YamlWorldRepository(
        worlds_path=app_root / "configuration" / "worlds",
    )
    world_resolver = WorldResolver(
        world_repository=world_repository,
    )
    language_response_policy = LanguageResponsePolicy()

    def factory() -> PrivateChatService:
        session = session_factory()
        repository = PostgreSQLPrivateChatRepository(session)

        return PrivateChatService(
            repository=repository,
            world_resolver=world_resolver,
            language_response_policy=language_response_policy,
            language_detector=language_detector,
            conversation_runtime=conversation_runtime,
            character_instruction=character_instruction,
            world_access_service=world_access_service,
        )

    return factory
