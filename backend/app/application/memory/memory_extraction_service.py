from __future__ import annotations

from typing import Any


class MemoryExtractionService:
    """
    Boundary between conversation events and Memory Engine.

    Does NOT:
    - call Telegram
    - call providers
    - bypass privacy controls
    - directly modify users
    """

    def __init__(
        self,
        *,
        memory_policy: Any,
    ) -> None:
        self._policy = memory_policy

    async def extract_candidate(
        self,
        *,
        conversation_events: list[Any],
    ):
        """
        Future implementation:
        Conversation Events ->
        Memory Candidate
        """
        return None
