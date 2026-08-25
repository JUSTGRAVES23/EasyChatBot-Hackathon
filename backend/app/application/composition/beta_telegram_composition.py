from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from backend.app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from backend.app.application.beta_access.beta_access_service import (
    BetaAccessService,
)
from backend.app.application.beta_access.beta_telegram_conversation_boundary import (
    BetaTelegramConversationBoundary,
)
from backend.app.application.beta_access.policies import (
    InMemoryTelegramAbuseProtector,
    InMemoryTelegramRateLimiter,
    LoggingTelegramObservability,
)
from backend.app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)
from backend.app.interfaces.telegram.beta_private_chat_gate import (
    BetaPrivateChatGate,
)
from backend.app.interfaces.telegram.beta_start_handler import (
    BetaTelegramStartHandler,
)
from backend.app.interfaces.telegram.beta_telegram_adapter import (
    BetaTelegramAdapter,
)
from backend.app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
)
from backend.app.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)


@dataclass(frozen=True)
class BetaTelegramComposition:
    """Fully composed Beta Telegram classroom application graph."""

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
    expiration_minutes: int = 1440,
    conversation_runtime: ConversationRuntime | None = None,
    conversation_runtime_factory: (
        Callable[[], ConversationRuntime] | None
    ) = None,
    rate_limiter: Any | None = None,
    abuse_protector: Any | None = None,
    observability: Any | None = None,
) -> BetaTelegramComposition:
    """Compose the production Beta Telegram classroom graph.

    Policy components are injected at the application boundary and never
    placed inside TelegramConversationService.
    """

    if expiration_minutes <= 0:
        raise ValueError(
            "expiration_minutes must be greater than zero."
        )

    if (
        conversation_runtime is not None
        and conversation_runtime_factory is not None
    ):
        raise ValueError(
            "Provide either conversation_runtime or "
            "conversation_runtime_factory, not both."
        )

    beta_access_service = BetaAccessService(
        user_repository=user_repository,
        token_repository=token_repository,
        binding_repository=binding_repository,
        expiration_minutes=expiration_minutes,
    )

    if conversation_runtime is not None:
        resolved_conversation_runtime = conversation_runtime
    elif conversation_runtime_factory is not None:
        resolved_conversation_runtime = conversation_runtime_factory()
    else:
        resolved_conversation_runtime = ConversationRuntime(
            llm_provider=LLMProviderFactory.create(),
        )

    conversation_service = TelegramConversationService(
        conversation_runtime=resolved_conversation_runtime,
        conversation_event_repository=conversation_event_repository,
        privacy_identifier_service=privacy_identifier_service,
        conversation_event_validator=conversation_event_validator,
    )

    resolved_rate_limiter = rate_limiter
    resolved_abuse_protector = abuse_protector
    resolved_observability = observability

    # Defaults are created here, at the composition boundary, so unit tests
    # can inject controlled doubles without changing application policy.
    if resolved_rate_limiter is None:
        resolved_rate_limiter = InMemoryTelegramRateLimiter(
            max_messages=_env_positive_int(
                "TELEGRAM_RATE_LIMIT_MAX_MESSAGES",
                100,
            ),
            window_seconds=_env_positive_float(
                "TELEGRAM_RATE_LIMIT_WINDOW_SECONDS",
                86400.0,
            ),
        )

    if resolved_abuse_protector is None:
        resolved_abuse_protector = InMemoryTelegramAbuseProtector(
            max_messages=_env_positive_int(
                "TELEGRAM_ABUSE_MAX_MESSAGES",
                10,
            ),
            window_seconds=_env_positive_float(
                "TELEGRAM_ABUSE_WINDOW_SECONDS",
                60.0,
            ),
        )

    if resolved_observability is None:
        resolved_observability = LoggingTelegramObservability(
            privacy_identifier_service=privacy_identifier_service,
        )

    conversation_boundary = BetaTelegramConversationBoundary(
        conversation_service=conversation_service,
        beta_access_service=beta_access_service,
        rate_limiter=resolved_rate_limiter,
        abuse_protector=resolved_abuse_protector,
        observability=resolved_observability,
    )

    private_chat_gate = BetaPrivateChatGate(
        beta_access_service=beta_access_service,
    )

    start_handler = BetaTelegramStartHandler(
        beta_access_service=beta_access_service,
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
    )


__all__ = [
    "BetaTelegramComposition",
    "create_beta_telegram_composition",
]
