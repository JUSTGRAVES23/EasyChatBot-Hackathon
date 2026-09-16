"""
Voice Call Execution Coordinator.

Application orchestration boundary
for voice call execution.

Responsibilities:
- Prepare voice room.
- Coordinate runtime execution.

Does NOT:
- Handle HTTP.
- Manage providers.
- Persist data.
- Connect LiveKit directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.application.uai.voice.voice_room_service import (
    VoiceRoomService,
)


from app.ai_runtime.voice.voice_call_execution_runtime import (
    VoiceCallExecutionRuntime,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallExecutionCoordinator:
    """
    Coordinates voice call execution.

    Keeps compatibility with the current
    application contracts.

    Future migration target:

        Lifecycle
            |
            â†“
        ExecutionService
            |
            â†“
        Runtime
    """


    room_service: VoiceRoomService

    execution_runtime: VoiceCallExecutionRuntime



    def start(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Prepare room and execute runtime.
        """


        room = (
            self.room_service
            .prepare_room(
                context=context,
            )
        )


        session = (
            self.execution_runtime
            .start(
                context=context,
            )
        )


        return {
            "room": room,
            "session": session,
        }



    def prepare(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Prepare room only.
        """


        return (
            self.room_service
            .prepare_room(
                context=context,
            )
        )



__all__ = [
    "VoiceCallExecutionCoordinator",
]

