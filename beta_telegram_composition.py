from __future__ import annotations

from dataclasses import dataclass
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
from app.application.beta_access.telegram_conversation_service import (
    TelegramConversationService,
)
from app.infrastructure.telegram.telegram_bot_runtime import (
    TelegramBotRuntime,
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
from app.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)


@dataclass(frozen=True)
class BetaTelegramComposition:
    """
    Fully composed Beta Telegram classroom application graph.

    This class composes the application graph only.
    It does not start Telegram polling.
    """

    beta_access_service: BetaAccessService
    conversation_runtime: ConversationRuntime
    conversation_service: TelegramConversationService
    conversation_boundary: BetaTelegramConversationBoundary
    private_chat_gate: BetaPrivateChatGate
    start_handler: BetaTelegramStartHandler
    adapter: BetaTelegramAdapter
    runtime: TelegramBotRuntime


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
) -> BetaTelegramComposition:
    """
    Compose the complete Beta Telegram classroom graph.

    Runtime resolution order:

        explicit conversation_runtime
                    â†“
        conversation_runtime_factory
                    â†“
        production ConversationRuntime

    The default production runtime uses the platform LLM provider
    abstraction and therefore does not bind Telegram directly to a
    provider.

    Dependency direction:

        Infrastructure
              â†“
        Application services
              â†“
        AI Runtime
              â†“
        Provider abstraction
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

    # =========================================================
    # BETA ACCESS
    # =========================================================

    beta_access_service = BetaAccessService(
        user_repository=user_repository,
        token_repository=token_repository,
        binding_repository=binding_repository,
        expiration_minutes=expiration_minutes,
    )

    # =========================================================
    # CONVERSATION RUNTIME
    # =========================================================

    if conversation_runtime is not None:
        resolved_conversation_runtime = conversation_runtime

    elif conversation_runtime_factory is not None:
        resolved_conversation_runtime = (
            conversation_runtime_factory()
        )

    else:
        resolved_conversation_runtime = ConversationRuntime(
            llm_provider=LLMProviderFactory.create(),
        )

    # =========================================================
    # CONVERSATION SERVICE
    # =========================================================

    conversation_service = TelegramConversationService(
        conversation_runtime=resolved_conversation_runtime,
        conversation_event_repository=(
            conversation_event_repository
        ),
        privacy_identifier_service=(
            privacy_identifier_service
        ),
        conversation_event_validator=(
            conversation_event_validator
        ),
    )

    # =========================================================
    # CONVERSATION BOUNDARY
    # =========================================================

    conversation_boundary = (
        BetaTelegramConversationBoundary(
            conversation_service=conversation_service,
            beta_access_service=beta_access_service,
        )
    )

    # =========================================================
    # PRIVATE CHAT GATE
    # =========================================================

    private_chat_gate = BetaPrivateChatGate(
        beta_access_service=beta_access_service,
    )

    # =========================================================
    # TELEGRAM START HANDLER
    # =========================================================

    start_handler = BetaTelegramStartHandler(
        beta_access_service=beta_access_service,
    )

    # =========================================================
    # TELEGRAM ADAPTER
    # =========================================================

    adapter = BetaTelegramAdapter(
        start_handler=start_handler,
        private_chat_gate=private_chat_gate,
        conversation_boundary=conversation_boundary,
    )

    # =========================================================
    # TELEGRAM RUNTIME
    # =========================================================

    runtime = TelegramBotRuntime(
        adapter=adapter,
        conversation_boundary=conversation_boundary,
    )

    return BetaTelegramComposition(
        beta_access_service=beta_access_service,
        conversation_runtime=(
            resolved_conversation_runtime
        ),
        conversation_service=conversation_service,
        conversation_boundary=conversation_boundary,
        private_chat_gate=private_chat_gate,
        start_handler=start_handler,
        adapter=adapter,
        runtime=runtime,
    )


__all__ = [
    "BetaTelegramComposition",
    "create_beta_telegram_composition",
]
