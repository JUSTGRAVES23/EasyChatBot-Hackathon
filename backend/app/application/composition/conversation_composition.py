from __future__ import annotations

from app.ai_runtime.conversation.conversation_runtime import (
    ConversationRuntime,
)
from app.providers.llm.llm_provider_factory import (
    LLMProviderFactory,
)


def create_conversation_runtime() -> ConversationRuntime:
    """
    Create shared ConversationRuntime.

    Composition layer responsibility.

    Channels:
    - Telegram
    - Voice
    - Future channels

    This function does not:
    - execute conversations
    - store memory
    - manage transport
    """

    return ConversationRuntime(
        llm_provider=(
            LLMProviderFactory.create()
        )
    )