
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.application.composition.beta_telegram_composition import (
    BetaTelegramComposition,
    create_beta_telegram_composition,
)
from app.application.composition.private_chat_composition import (
    build_private_chat_service_factory,
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
from app.application.services.beta_world_access_service import (
    BetaWorldAccessService,
)
from app.application.services.world_access_service import (
    WorldAccessService,
)
from app.application.study_material.service import StudyMaterialService
from app.application.uai.language.language_detector import LanguageDetector
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.application.uai.world.world_resolver import WorldResolver
from app.application.world_catalogue.service import (
    LearningWorldCatalogueService,
)
from app.application.world_telegram.world_telegram_start_router import (
    WorldTelegramStartRouter,
)
from app.application.world_telegram.community_access_service import (
    WorldTelegramCommunityAccessService,
)
from app.application.world_telegram.community_conversation_boundary import (
    WorldTelegramCommunityConversationBoundary,
)
from app.application.world_telegram.membership_service import (
    WorldTelegramMembershipService,
)
from app.infrastructure.auth.postgresql_auth_repository import (
    PostgreSQLAuthenticationRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
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
from app.infrastructure.persistence.postgresql_telegram_update_idempotency_repository import (
    PostgreSQLTelegramUpdateIdempotencyRepository,
)
from app.infrastructure.persistence.postgresql_learner_world_access_repository import (
    PostgreSQLLearnerWorldAccessRepository,
)
from app.infrastructure.persistence.postgresql_learning_world_catalogue_repository import (
    PostgreSQLLearningWorldCatalogueRepository,
)
from app.infrastructure.persistence.postgresql_provider_usage_repository import (
    PostgreSQLProviderUsageRepository,
)
from app.infrastructure.persistence.postgresql_study_material_repository import (
    PostgreSQLStudyMaterialRepository,
)
from app.infrastructure.persistence.postgresql_world_telegram_destination_repository import (
    PostgreSQLWorldTelegramDestinationRepository,
)
from app.infrastructure.persistence.postgresql_world_telegram_membership_repository import (
    PostgreSQLWorldTelegramMembershipRepository,
)
from app.infrastructure.telegram.telegram_bot_runtime import TelegramBotRuntime
from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BetaTelegramProductionComposition:
    beta_telegram: BetaTelegramComposition
    database_engine: Any
    session_factory: Any
    async_database_engine: Any
    async_session_factory: Any
    catalogue_service: LearningWorldCatalogueService
    study_material_service: StudyMaterialService
    world_telegram_community_access_service: (
        WorldTelegramCommunityAccessService
    )
    world_telegram_community_conversation_boundary: (
        WorldTelegramCommunityConversationBoundary
    )

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
    def beta_world_access_service(
        self,
    ) -> BetaWorldAccessService:
        return self.beta_telegram.beta_world_access_service

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

    @property
    def community_conversation_boundary(
        self,
    ) -> WorldTelegramCommunityConversationBoundary:
        return self.world_telegram_community_conversation_boundary


def create_production_beta_telegram_composition(
    *,
    expiration_minutes: int = 1440,
    database_engine: Any | None = None,
    session_factory: Any | None = None,
    database_engine_factory: Callable[[], Any] | None = None,
    session_factory_factory: Callable[[Any], Any] | None = None,
    async_database_engine: Any | None = None,
    async_session_factory: Any | None = None,
    conversation_runtime: ConversationRuntime | None = None,
    conversation_runtime_factory: (
        Callable[[], ConversationRuntime] | None
    ) = None,
    functionality_control_service: (
        FunctionalityOperationalControlService | None
    ) = None,
    language_detector: LanguageDetector | None = None,
) -> BetaTelegramProductionComposition:
    """
    Create the production Beta Telegram composition.

    W18.3 production provisioning is wired here.

    W19.3 controlled World Telegram community access and W19.4
    community conversation boundary are composed here, but remain
    outside the private Telegram transport/runtime boundary.

    Responsibilities:
    - Build the existing synchronous Beta Telegram persistence boundary.
    - Build the canonical asynchronous authentication boundary.
    - Reuse the existing learner/world access repository.
    - Build WorldAccessService from the canonical repositories.
    - Build BetaWorldAccessService from the canonical Beta user,
      World catalogue and World access services.
    - Build the W19.3 World Telegram destination and membership
      persistence boundaries.
    - Build the W19.3 controlled community access application service.
    - Build the W19.4 community conversation boundary.
    - Inject BetaWorldAccessService into the canonical Telegram
      composition.

    Telegram remains responsible only for onboarding/binding and
    existing private-chat conversation handling.

    W19.3 does not register Telegram group handlers, call the
    Telegram API, grant World access, or invoke the AI runtime.

    W19.4 only authorizes registered community conversation context;
    it does not register Telegram handlers, call the Telegram API,
    create membership, grant World access, or invoke the AI runtime.
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

    if language_detector is None:
        raise ValueError(
            "language_detector is required "
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

    if async_database_engine is None:
        async_database_engine = create_async_database_engine()

    if async_session_factory is None:
        async_session_factory = create_async_session_factory(
            async_database_engine
        )

    # ------------------------------------------------------------------
    # Existing Beta Telegram persistence
    # ------------------------------------------------------------------

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

    provider_usage_repository = (
        PostgreSQLProviderUsageRepository(
            session_factory,
        )
    )

    # ------------------------------------------------------------------
    # W19.10 Telegram inbound update idempotency
    # ------------------------------------------------------------------

    telegram_update_idempotency = (
        PostgreSQLTelegramUpdateIdempotencyRepository(
            session_factory=session_factory,
        )
    )

    # ------------------------------------------------------------------
    # Canonical World infrastructure
    # ------------------------------------------------------------------

    app_root = Path(__file__).resolve().parents[2]

    world_repository = YamlWorldRepository(
        worlds_path=(
            app_root
            / "configuration"
            / "worlds"
        )
    )

    world_resolver = WorldResolver(
        world_repository=world_repository,
    )

    catalogue_repository = (
        PostgreSQLLearningWorldCatalogueRepository(
            session_factory,
        )
    )

    catalogue_service = LearningWorldCatalogueService(
        repository=catalogue_repository,
        world_resolver=world_resolver,
    )

    # ------------------------------------------------------------------
    # W18.3 World authorization/provisioning
    # ------------------------------------------------------------------

    authentication_repository = (
        PostgreSQLAuthenticationRepository(
            async_session_factory,
        )
    )

    learner_world_access_repository = (
        PostgreSQLLearnerWorldAccessRepository(
            session_factory,
        )
    )

    world_access_service = WorldAccessService(
        access_repository=learner_world_access_repository,
        user_identity_reader=authentication_repository,
        learning_world_repository=catalogue_repository,
    )

    # ------------------------------------------------------------------
    # W19.3 Controlled World Telegram community access
    # ------------------------------------------------------------------

    world_telegram_destination_repository = (
        PostgreSQLWorldTelegramDestinationRepository(
            session_factory,
        )
    )

    world_telegram_membership_repository = (
        PostgreSQLWorldTelegramMembershipRepository(
            session_factory,
        )
    )

    world_telegram_membership_service = (
        WorldTelegramMembershipService(
            repository=world_telegram_membership_repository,
            destination_repository=(
                world_telegram_destination_repository
            ),
        )
    )

    world_telegram_community_access_service = (
        WorldTelegramCommunityAccessService(
            world_access_service=world_access_service,
            world_catalogue_repository=catalogue_repository,
            destination_repository=(
                world_telegram_destination_repository
            ),
            membership_service=world_telegram_membership_service,
        )
    )

    world_telegram_community_conversation_boundary = (
        WorldTelegramCommunityConversationBoundary(
            world_access_service=world_access_service,
            world_catalogue_repository=catalogue_repository,
            destination_repository=(
                world_telegram_destination_repository
            ),
            membership_service=world_telegram_membership_service,
        )
    )

    # ------------------------------------------------------------------
    # Beta World authorization/provisioning
    # ------------------------------------------------------------------

    beta_world_access_service = BetaWorldAccessService(
        beta_user_reader=beta_user_repository,
        user_identity_reader=authentication_repository,
        world_catalogue=catalogue_repository,
        world_access=world_access_service,
    )

    # ------------------------------------------------------------------
    # Study Materials
    # ------------------------------------------------------------------

    privacy_identifier_service = PrivacyIdentifierService()

    conversation_event_validator = (
        ConversationEventValidator()
    )

    study_material_repository = (
        PostgreSQLStudyMaterialRepository(
            session_factory,
        )
    )

    study_material_service = StudyMaterialService(
        repository=study_material_repository,
        world_catalogue_service=catalogue_service,
    )

    # ------------------------------------------------------------------
    # W19.5 Private Telegram chat
    # ------------------------------------------------------------------

    private_chat_character_instruction = os.getenv(
        "EASYCHATBOT_PRIVATE_CHAT_CHARACTER_INSTRUCTION",
        (
            "You are a helpful EasyChatBot learning character. "
            "Stay within the selected Learning World and follow its "
            "application-controlled language policy. "
            "Do not allow the learner to override World, provider, model, "
            "or other application-controlled settings."
        ),
    )

    if conversation_runtime is None:
        raise ValueError(
            "conversation_runtime is required for production "
            "private-chat composition."
        )

    private_chat_service_factory = (
        build_private_chat_service_factory(
            session_factory=session_factory,
            conversation_runtime=conversation_runtime,
            character_instruction=private_chat_character_instruction,
            language_detector=language_detector,
        )
    )

    # ------------------------------------------------------------------
    # W19.7 World Telegram start routing
    # ------------------------------------------------------------------

    world_start_router = WorldTelegramStartRouter(
        world_catalogue_service=catalogue_service,
    )

    # ------------------------------------------------------------------
    # Telegram application composition
    # ------------------------------------------------------------------

    beta_telegram = create_beta_telegram_composition(
        user_repository=beta_user_repository,
        token_repository=beta_token_repository,
        binding_repository=telegram_binding_repository,
        conversation_event_repository=(
            conversation_event_repository
        ),
        telegram_update_idempotency=(
            telegram_update_idempotency
        ),
        privacy_identifier_service=(
            privacy_identifier_service
        ),
        conversation_event_validator=(
            conversation_event_validator
        ),
        beta_world_access_service=(
            beta_world_access_service
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
        world_resolver=world_resolver,
        language_response_policy=(
            LanguageResponsePolicy()
        ),
        language_detector=language_detector,
        private_chat_service_factory=private_chat_service_factory,
        world_start_router=world_start_router,
    )

    logger.info(
        "Production Beta Telegram composition created "
        "with W18.3 complete World provisioning, "
        "W19.3 controlled World Telegram community access, "
        "W19.4 community conversation boundary, "
        "durable usage ledger, functionality control, "
        "Study Material service, and W19.10 inbound "
        "Telegram update idempotency."
    )

    return BetaTelegramProductionComposition(
        beta_telegram=beta_telegram,
        database_engine=database_engine,
        session_factory=session_factory,
        async_database_engine=async_database_engine,
        async_session_factory=async_session_factory,
        catalogue_service=catalogue_service,
        study_material_service=study_material_service,
        world_telegram_community_access_service=(
            world_telegram_community_access_service
        ),
        world_telegram_community_conversation_boundary=(
            world_telegram_community_conversation_boundary
        ),
    )


__all__ = [
    "BetaTelegramProductionComposition",
    "create_production_beta_telegram_composition",
]
