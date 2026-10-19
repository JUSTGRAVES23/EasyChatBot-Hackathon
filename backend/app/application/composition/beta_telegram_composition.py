from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from app.application.beta_access.policies import (
    InMemoryTelegramAbuseProtector,
    InMemoryTelegramRateLimiter,
    LoggingTelegramObservability,
)
from app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)
from app.application.ports.telegram_update_idempotency import (
    TelegramUpdateIdempotencyPort,
)
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.private_chat.telegram_private_chat_bridge import (
    TelegramPrivateChatBridge,
)
from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.application.services.beta_world_access_service import (
    BetaWorldAccessService,
)
from app.application.services.world_access_service import WorldAccessService
from app.application.uai.language.language_detector import (
    LanguageDetector,
)
from app.application.uai.language.language_response_policy import (
    LanguageResponsePolicy,
)
from app.application.uai.world.world_resolver import WorldResolver
from app.application.world_telegram.world_telegram_start_router import (
    WorldTelegramStartRouter,
)
from app.interfaces.telegram.beta_private_chat_gate import (
    BetaPrivateChatGate,
)
from app.interfaces.telegram.beta_start_handler import (
    BetaTelegramStartHandler,
)
from app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)
from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)
from app.infrastructure.worlds.yaml_world_repository import (
    YamlWorldRepository,
)
from app.providers.llm.llm_provider_factory import LLMProviderFactory
from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
    ProviderUsageRepository,
)
from src.ai_runtime.providers.usage.service import ProviderUsageService


@dataclass(frozen=True)
class BetaTelegramComposition:
    beta_access_service: BetaAccessService
    beta_world_access_service: BetaWorldAccessService
    conversation_runtime: ConversationRuntime
    conversation_service: TelegramConversationService
    conversation_boundary: BetaTelegramConversationBoundary
    private_chat_bridge: TelegramPrivateChatBridge | None
    private_chat_gate: BetaPrivateChatGate
    start_handler: BetaTelegramStartHandler
    adapter: BetaTelegramAdapter
    runtime: TelegramBotRuntime
    world_access_service: WorldAccessService | None = None
    rate_limiter: Any | None = None
    abuse_protector: Any | None = None
    observability: Any | None = None
    provider_usage_repository: ProviderUsageRepository | None = None


def _env_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name)

    if raw is None:
        return default

    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a positive integer."
        ) from exc

    if value <= 0:
        raise ValueError(
            f"{name} must be a positive integer."
        )

    return value


def _env_positive_float(name: str, default: float) -> float:
    raw = os.getenv(name)

    if raw is None:
        return default

    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a positive number."
        ) from exc

    if value <= 0:
        raise ValueError(
            f"{name} must be a positive number."
        )

    return value


def create_beta_telegram_composition(
    *,
    user_repository: Any,
    token_repository: Any,
    binding_repository: Any,
    conversation_event_repository: Any,
    privacy_identifier_service: Any,
    conversation_event_validator: Any,
    beta_world_access_service: BetaWorldAccessService,
    expiration_minutes: int = 1440,
    conversation_runtime: ConversationRuntime | None = None,
    conversation_runtime_factory: (
        Callable[[], ConversationRuntime] | None
    ) = None,
    rate_limiter: Any | None = None,
    abuse_protector: Any | None = None,
    observability: Any | None = None,
    provider_usage_capture: ProviderUsageCapture | None = None,
    provider_usage_repository: ProviderUsageRepository | None = None,
    functionality_control_service: (
        FunctionalityOperationalControlService | None
    ) = None,
    world_resolver: WorldResolver | None = None,
    language_response_policy: LanguageResponsePolicy | None = None,
    language_detector: LanguageDetector | None = None,
    private_chat_service_factory: Callable[[], Any] | None = None,
    world_access_service: WorldAccessService | None = None,
    world_start_router: WorldTelegramStartRouter | None = None,
    telegram_update_idempotency: (
        TelegramUpdateIdempotencyPort | None
    ) = None,
) -> BetaTelegramComposition:
    """Create the Beta Telegram application composition.

    BetaAccessService owns Telegram identity binding.

    BetaWorldAccessService owns durable provisioning of the complete
    Learning World portfolio after successful Beta onboarding.

    Telegram never selects or changes the user's active World.

    Telegram update idempotency is injected through the application
    port. The infrastructure implementation belongs to the production
    composition root.
    """

    if expiration_minutes <= 0:
        raise ValueError(
            "expiration_minutes must be greater than zero."
        )

    if beta_world_access_service is None:
        raise ValueError(
            "beta_world_access_service is required."
        )

    if (
        conversation_runtime is not None
        and conversation_runtime_factory is not None
    ):
        raise ValueError(
            "Provide either conversation_runtime or "
            "conversation_runtime_factory, not both."
        )

    # Application configuration root:
    #
    # backend/app
    #
    app_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    world_repository = YamlWorldRepository(
        worlds_path=(
            app_root
            / "configuration"
            / "worlds"
        )
    )

    if world_resolver is None:
        world_resolver = WorldResolver(
            world_repository=world_repository,
        )

    beta_access_service = BetaAccessService(
        user_repository=user_repository,
        token_repository=token_repository,
        binding_repository=binding_repository,
        world_resolver=world_resolver,
        expiration_minutes=expiration_minutes,
    )

    resolved_usage_repository = provider_usage_repository

    if conversation_runtime is not None:
        resolved_conversation_runtime = conversation_runtime

    elif conversation_runtime_factory is not None:
        resolved_conversation_runtime = conversation_runtime_factory()

        # P1.6.1: when production supplies a durable usage repository,
        # attach usage capture to the factory-created ConversationRuntime.
        # Keep the existing factory API and explicit runtime injection seam.
        if (
            provider_usage_repository is not None
            and provider_usage_capture is None
            and isinstance(
                resolved_conversation_runtime,
                ConversationRuntime,
            )
            and resolved_conversation_runtime.usage_capture is None
        ):
            provider_usage_service = ProviderUsageService(
                provider_usage_repository
            )

            provider_usage_capture = ProviderUsageCapture(
                provider_usage_service
            )

            resolved_conversation_runtime = replace(
                resolved_conversation_runtime,
                usage_capture=provider_usage_capture,
                usage_context=ProviderUsageContext(
                    capability="conversation",
                    functionality="chat",
                    agent="conversation_agent",
                ),
            )

    else:
        if provider_usage_capture is None:
            if resolved_usage_repository is None:
                resolved_usage_repository = (
                    InMemoryProviderUsageRepository()
                )

            provider_usage_service = ProviderUsageService(
                resolved_usage_repository
            )

            provider_usage_capture = ProviderUsageCapture(
                provider_usage_service
            )

        resolved_conversation_runtime = ConversationRuntime(
            llm_provider=LLMProviderFactory.create(),
            usage_capture=provider_usage_capture,
            usage_context=ProviderUsageContext(
                capability="conversation",
                functionality="chat",
                agent="conversation_agent",
            ),
        )

    resolved_language_response_policy = (
        language_response_policy
        or LanguageResponsePolicy()
    )

    if language_detector is None:
        raise ValueError(
            "language_detector is required for "
            "Beta Telegram composition."
        )

    conversation_service = TelegramConversationService(
        conversation_runtime=resolved_conversation_runtime,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        conversation_event_validator=conversation_event_validator,
        language_response_policy=resolved_language_response_policy,
        language_detector=language_detector,
        world_resolver=world_resolver,
    )

    resolved_rate_limiter = (
        rate_limiter
        or InMemoryTelegramRateLimiter(
            max_messages=_env_positive_int(
                "TELEGRAM_RATE_LIMIT_MAX_MESSAGES",
                100,
            ),
            window_seconds=_env_positive_float(
                "TELEGRAM_RATE_LIMIT_WINDOW_SECONDS",
                86400.0,
            ),
        )
    )

    resolved_abuse_protector = (
        abuse_protector
        or InMemoryTelegramAbuseProtector(
            max_messages=_env_positive_int(
                "TELEGRAM_ABUSE_MAX_MESSAGES",
                10,
            ),
            window_seconds=_env_positive_float(
                "TELEGRAM_ABUSE_WINDOW_SECONDS",
                60.0,
            ),
        )
    )

    resolved_observability = (
        observability
        or LoggingTelegramObservability(
            privacy_identifier_service=privacy_identifier_service,
        )
    )

    private_chat_bridge = None

    if private_chat_service_factory is not None:
        if world_access_service is None:
            raise ValueError(
                "world_access_service is required when "
                "private_chat_service_factory is configured."
            )
        private_chat_bridge = TelegramPrivateChatBridge(
            private_chat_service_factory=private_chat_service_factory,
        )

    conversation_boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=beta_access_service,
        rate_limiter=resolved_rate_limiter,
        abuse_protector=resolved_abuse_protector,
        observability=resolved_observability,
        functionality_control_service=functionality_control_service,
        private_chat_bridge=private_chat_bridge,
        world_access_service=world_access_service,
    )

    private_chat_gate = BetaPrivateChatGate(
        beta_access_service=beta_access_service,
    )

    start_handler = BetaTelegramStartHandler(
        beta_access_service=beta_access_service,
        beta_world_access_service=beta_world_access_service,
        privacy_identifier_service=privacy_identifier_service,
    )

    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=private_chat_gate,
        conversation_boundary=conversation_boundary,
        world_start_router=world_start_router,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=conversation_boundary,
        telegram_update_idempotency=telegram_update_idempotency,
    )

    return BetaTelegramComposition(
        beta_access_service=beta_access_service,
        beta_world_access_service=beta_world_access_service,
        conversation_runtime=resolved_conversation_runtime,
        conversation_service=conversation_service,
        conversation_boundary=conversation_boundary,
        private_chat_bridge=private_chat_bridge,
        world_access_service=world_access_service,
        private_chat_gate=private_chat_gate,
        start_handler=start_handler,
        adapter=adapter,
        runtime=runtime,
        rate_limiter=resolved_rate_limiter,
        abuse_protector=resolved_abuse_protector,
        observability=resolved_observability,
        provider_usage_repository=resolved_usage_repository,
    )


__all__ = [
    "BetaTelegramComposition",
    "create_beta_telegram_composition",
]
