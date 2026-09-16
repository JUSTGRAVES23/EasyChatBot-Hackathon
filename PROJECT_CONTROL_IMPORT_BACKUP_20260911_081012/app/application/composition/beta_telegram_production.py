from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.application.composition.beta_telegram_composition import (
    BetaTelegramComposition,
    create_beta_telegram_composition,
)
from app.application.conversation_quality.conversation_event_validator import (
    ConversationEventValidator,
)
from app.application.privacy.privacy_identifier_service import (
    PrivacyIdentifierService,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.persistence.postgresql_beta_access_repository import (
    PostgreSQLBetaTokenRepository,
    PostgreSQLBetaUserRepository,
    PostgreSQLTelegramBindingRepository,
)
from app.infrastructure.persistence.postgresql_conversation_event_repository import (
    PostgreSQLConversationEventRepository,
)
from app.infrastructure.persistence.postgresql_provider_usage_repository import (
    PostgreSQLProviderUsageRepository,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BetaTelegramProductionComposition:
    beta_telegram: BetaTelegramComposition
    database_engine: Any
    session_factory: Any

    @property
    def runtime(self) -> Any:
        return self.beta_telegram.runtime

    @property
    def adapter(self) -> Any:
        return self.beta_telegram.adapter

    @property
    def beta_access_service(self) -> Any:
        return self.beta_telegram.beta_access_service

    @property
    def conversation_runtime(self) -> Any:
        return self.beta_telegram.conversation_runtime

    @property
    def conversation_service(self) -> Any:
        return self.beta_telegram.conversation_service

    @property
    def conversation_boundary(self) -> Any:
        return self.beta_telegram.conversation_boundary

    @property
    def private_chat_gate(self) -> Any:
        return self.beta_telegram.private_chat_gate

    @property
    def start_handler(self) -> Any:
        return self.beta_telegram.start_handler


def create_production_beta_telegram_composition(
    *,
    expiration_minutes: int = 1440,
    database_engine: Any | None = None,
    session_factory: Any | None = None,
    database_engine_factory: Callable[[], Any] | None = None,
    session_factory_factory: Callable[[Any], Any] | None = None,
    conversation_runtime: ConversationRuntime | None = None,
    conversation_runtime_factory: Callable[[], ConversationRuntime] | None = None,
    functionality_control_service: (
        FunctionalityOperationalControlService | None
    ) = None,
) -> BetaTelegramProductionComposition:
    """Create the production Beta Telegram composition.

    Production Telegram processing requires the operational
    functionality-control service. The service is injected from
    the application composition; this factory never creates a
    second control service or control repository.
    """

    if expiration_minutes <= 0:
        raise ValueError(
            "expiration_minutes must be greater than zero."
        )

    if functionality_control_service is None:
        raise ValueError(
            "functionality_control_service is required "
            "for production Telegram composition."
        )

    if (
        database_engine is not None
        and database_engine_factory is not None
    ):
        raise ValueError(
            "Provide either database_engine or "
            "database_engine_factory, not both."
        )

    if (
        session_factory is not None
        and session_factory_factory is not None
    ):
        raise ValueError(
            "Provide either session_factory or "
            "session_factory_factory, not both."
        )

    if (
        conversation_runtime is not None
        and conversation_runtime_factory is not None
    ):
        raise ValueError(
            "Provide either conversation_runtime or "
            "conversation_runtime_factory, not both."
        )

    if database_engine is None:
        database_engine = (
            database_engine_factory
            or create_database_engine
        )()

    if session_factory is None:
        session_factory = (
            session_factory_factory
            or create_session_factory
        )(database_engine)

    beta_user_repository = PostgreSQLBetaUserRepository(
        session_factory,
    )
    beta_token_repository = PostgreSQLBetaTokenRepository(
        session_factory,
    )
    telegram_binding_repository = (
        PostgreSQLTelegramBindingRepository(
            session_factory,
        )
    )
    conversation_event_repository = (
        PostgreSQLConversationEventRepository(
            session_factory,
        )
    )

    # Durable provider usage ledger.
    # Accounting remains outside the Operations Center.
    provider_usage_repository = (
        PostgreSQLProviderUsageRepository(
            session_factory,
        )
    )

    privacy_identifier_service = PrivacyIdentifierService()
    conversation_event_validator = (
        ConversationEventValidator()
    )

    beta_telegram = create_beta_telegram_composition(
        user_repository=beta_user_repository,
        token_repository=beta_token_repository,
        binding_repository=telegram_binding_repository,
        conversation_event_repository=(
            conversation_event_repository
        ),
        privacy_identifier_service=(
            privacy_identifier_service
        ),
        conversation_event_validator=(
            conversation_event_validator
        ),
        expiration_minutes=expiration_minutes,
        conversation_runtime=conversation_runtime,
        conversation_runtime_factory=(
            conversation_runtime_factory
        ),
        provider_usage_repository=(
            provider_usage_repository
        ),
        functionality_control_service=(
            functionality_control_service
        ),
    )

    logger.info(
        "Production Beta Telegram composition created "
        "with durable usage ledger and functionality control."
    )

    return BetaTelegramProductionComposition(
        beta_telegram=beta_telegram,
        database_engine=database_engine,
        session_factory=session_factory,
    )


__all__ = [
    "BetaTelegramProductionComposition",
    "create_production_beta_telegram_composition",
]

