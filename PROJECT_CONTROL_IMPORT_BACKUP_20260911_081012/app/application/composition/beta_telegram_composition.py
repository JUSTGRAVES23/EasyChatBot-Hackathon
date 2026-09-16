from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Any, Callable

from app.ai_runtime.conversation.conversation_runtime import ConversationRuntime
from app.application.beta_access.beta_access_service import BetaAccessService
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
from app.application.provider_management.functionality_operational_control_service import (
    FunctionalityOperationalControlService,
)
from app.application.providers.provider_usage_capture import (
    ProviderUsageCapture,
    ProviderUsageContext,
)
from app.interfaces.telegram.beta_private_chat_gate import BetaPrivateChatGate
from app.interfaces.telegram.beta_start_handler import BetaTelegramStartHandler
from app.interfaces.telegram.beta_telegram_adapter import BetaTelegramAdapter
from app.infrastructure.telegram.telegram_bot_runtime import TelegramBotRuntime
from app.providers.llm.llm_provider_factory import LLMProviderFactory
from src.ai_runtime.providers.usage.repository import (
    InMemoryProviderUsageRepository,
    ProviderUsageRepository,
)
from src.ai_runtime.providers.usage.service import ProviderUsageService


@dataclass(frozen=True)
class BetaTelegramComposition:
    beta_access_service: BetaAccessService
    conversation_runtime: ConversationRuntime
    conversation_service: TelegramConversationService
    conversation_boundary: BetaTelegramConversationBoundary
    private_chat_gate: BetaPrivateChatGate
    start_handler: BetaTelegramStartHandler
    adapter: BetaTelegramAdapter
    runtime: TelegramBotRuntime
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
        raise ValueError(f"{name} must be a positive integer.") from exc
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _env_positive_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number.") from exc
    if value <= 0:
        raise ValueError(f"{name} must be a positive number.")
    return value


def create_beta_telegram_composition(
    *,
    user_repository: Any,
    token_repository: Any,
    binding_repository: Any,
    conversation_event_repository: Any,
    privacy_identifier_service: Any,
    conversation_event_validator: Any,
    expiration_minutes: int = 1440,
    conversation_runtime: ConversationRuntime | None = None,
    conversation_runtime_factory: Callable[[], ConversationRuntime] | None = None,
    rate_limiter: Any | None = None,
    abuse_protector: Any | None = None,
    observability: Any | None = None,
    provider_usage_capture: ProviderUsageCapture | None = None,
    provider_usage_repository: ProviderUsageRepository | None = None,
    functionality_control_service: (
        FunctionalityOperationalControlService | None
    ) = None,
) -> BetaTelegramComposition:
    """Create the Beta Telegram application composition.

    ``functionality_control_service`` is optional at this lower-level
    composition boundary so isolated application/unit compositions can
    continue to construct Telegram without requiring infrastructure.

    Production composition is responsible for requiring and supplying
    the authoritative functionality-control service.
    """

    if expiration_minutes <= 0:
        raise ValueError("expiration_minutes must be greater than zero.")

    if conversation_runtime is not None and conversation_runtime_factory is not None:
        raise ValueError(
            "Provide either conversation_runtime or conversation_runtime_factory, not both."
        )

    beta_access_service = BetaAccessService(
        user_repository=user_repository,
        token_repository=token_repository,
        binding_repository=binding_repository,
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
            and isinstance(resolved_conversation_runtime, ConversationRuntime)
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
                resolved_usage_repository = InMemoryProviderUsageRepository()

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

    conversation_service = TelegramConversationService(
        conversation_runtime=resolved_conversation_runtime,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        conversation_event_validator=conversation_event_validator,
    )

    resolved_rate_limiter = rate_limiter or InMemoryTelegramRateLimiter(
        max_messages=_env_positive_int(
            "TELEGRAM_RATE_LIMIT_MAX_MESSAGES",
            100,
        ),
        window_seconds=_env_positive_float(
            "TELEGRAM_RATE_LIMIT_WINDOW_SECONDS",
            86400.0,
        ),
    )

    resolved_abuse_protector = abuse_protector or InMemoryTelegramAbuseProtector(
        max_messages=_env_positive_int(
            "TELEGRAM_ABUSE_MAX_MESSAGES",
            10,
        ),
        window_seconds=_env_positive_float(
            "TELEGRAM_ABUSE_WINDOW_SECONDS",
            60.0,
        ),
    )

    resolved_observability = observability or LoggingTelegramObservability(
        privacy_identifier_service=privacy_identifier_service,
    )

    conversation_boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=beta_access_service,
        rate_limiter=resolved_rate_limiter,
        abuse_protector=resolved_abuse_protector,
        observability=resolved_observability,
        functionality_control_service=functionality_control_service,
    )

    private_chat_gate = BetaPrivateChatGate(
        beta_access_service=beta_access_service
    )

    start_handler = BetaTelegramStartHandler(
        beta_access_service=beta_access_service
    )

    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=private_chat_gate,
        conversation_boundary=conversation_boundary,
    )

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=conversation_boundary,
    )

    return BetaTelegramComposition(
        beta_access_service=beta_access_service,
        conversation_runtime=resolved_conversation_runtime,
        conversation_service=conversation_service,
        conversation_boundary=conversation_boundary,
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

