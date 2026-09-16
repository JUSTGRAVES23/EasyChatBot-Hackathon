from __future__ import annotations

from typing import Any


class RuntimeEngine:
    """Legacy/simple RuntimeEngine retained for existing integrations.

    This component directly invokes an agent and represents a different
    execution generation from the governed runtime path.
    """

    async def execute(self, *, agent: Any, context: Any) -> Any:
        if agent is None:
            raise ValueError("agent is required")
        if context is None:
            raise ValueError("context is required")
        return await agent.execute(context)
