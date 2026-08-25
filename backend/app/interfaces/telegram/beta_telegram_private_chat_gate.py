from __future__ import annotations

from .beta_private_chat_gate import BetaPrivateChatGate


class BetaTelegramPrivateChatGate(BetaPrivateChatGate):
    """Backward-compatible alias for the Beta private-chat gate.

    New code should depend on BetaPrivateChatGate. The alias is retained
    so existing imports do not break during the Beta 1 migration.
    """


__all__ = ["BetaTelegramPrivateChatGate"]
