"""
Voice Room Service.

Application service responsible for
preparing voice room configuration.

Responsibilities:
- Coordinate execution context.
- Request room preparation.
- Return provider-independent
  room configuration.

Does NOT:
- Handle HTTP.
- Execute AI.
- Manage providers directly.
- Persist data.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.uai.voice.voice_room_port import (
    VoiceRoomPort,
)
from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


@dataclass(
    frozen=True,
    slots=True,
)
class VoiceRoomService:
    """
    Application boundary for
    voice room preparation.
    """

    room_adapter: VoiceRoomPort

    def prepare_room(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Prepare room configuration.
        """

        return (
            self.room_adapter
            .create_room_configuration(
                context=context,
            )
        )


__all__ = [
    "VoiceRoomService",
]

