from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.application.composition.beta_telegram_composition import (
    BetaTelegramComposition,
    create_beta_telegram_composition,
)
from backend.app.application.conversation_quality.conversation_event_validator import (
    ConversationEventValidator,
)
from backend.app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)
from backend.app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from backend.app.infrastructure.persistence.postgresql_beta_access_repository import (
    PostgreSQLBetaTokenRepository,
    PostgreSQLBetaUserRepository,
    PostgreSQLTelegramBindingRepository,
)
from backend.app.infrastructure.persistence.postgresql_conversation_event_repository import (
    PostgreSQLConversationEventRepository,
)


@dataclass(frozen=True)
class BetaTelegramProductionComposition:
    """Complete production dependency graph for Beta Telegram."""

    database_engine: Any
    session_factory: Any
    beta_user_repository: PostgreSQLBetaUserRepository
    beta_token_repository: PostgreSQLBetaTokenRepository
    telegram_binding_repository: PostgreSQLTelegramBindingRepository
    conversation_event_repository: PostgreSQLConversationEventRepository
    privacy_identifier_service: PrivacyIdentifierService
    conversation_event_validator: ConversationEventValidator
    beta_telegram: BetaTelegramComposition


def create_production_beta_telegram_composition(
    *,
    expiration_minutes: int = 1440,
) -> BetaTelegramProductionComposition:
    """Build the production Beta Telegram dependency graph.

    The function creates dependencies only; it does not start
    Telegram polling or perform external side effects.
    """
    if expiration_minutes <= 0:
        raise ValueError(
            "expiration_minutes must be greater than zero."
        )

    database_engine = create_database_engine()
    session_factory = create_session_factory(database_engine)

    beta_user_repository = PostgreSQLBetaUserRepository(
        session_factory,
    )
    beta_token_repository = PostgreSQLBetaTokenRepository(
        session_factory,
    )
    telegram_binding_repository = PostgreSQLTelegramBindingRepository(
        session_factory,
    )
    conversation_event_repository = PostgreSQLConversationEventRepository(
        session_factory,
    )

    privacy_identifier_service = PrivacyIdentifierService()
    conversation_event_validator = ConversationEventValidator()

    beta_telegram = create_beta_telegram_composition(
        user_repository=beta_user_repository,
        token_repository=beta_token_repository,
        binding_repository=telegram_binding_repository,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        conversation_event_validator=conversation_event_validator,
        expiration_minutes=expiration_minutes,
    )

    return BetaTelegramProductionComposition(
        database_engine=database_engine,
        session_factory=session_factory,
        beta_user_repository=beta_user_repository,
        beta_token_repository=beta_token_repository,
        telegram_binding_repository=telegram_binding_repository,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        conversation_event_validator=conversation_event_validator,
        beta_telegram=beta_telegram,
    )


__all__ = [
    "BetaTelegramProductionComposition",
    "create_production_beta_telegram_composition",
]