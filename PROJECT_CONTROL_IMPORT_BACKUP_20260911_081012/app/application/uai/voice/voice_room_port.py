"""
Voice Room Port.

Application-owned abstraction for voice room
infrastructure.

The application layer depends on this contract,
not on a concrete provider adapter.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


class VoiceRoomPort(Protocol):
    """
    Application-facing contract for voice room preparation.

    Infrastructure adapters implement this contract
    through Python structural typing.
    """

    def create_room_configuration(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Create provider-independent room configuration.
        """
        ...


__all__ = [
    "VoiceRoomPort",
]

