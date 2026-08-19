"""
Voice Call Execution Coordinator.

Application orchestration boundary
between room preparation and runtime
execution.

Responsibilities:
- Prepare room.
- Start voice execution.
- Coordinate application services.

Does NOT:
- Handle HTTP.
- Manage providers.
- Execute audio directly.
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


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallExecutionCoordinator:
    """
    Coordinates complete voice execution flow.
    """

    room_service: VoiceRoomService

    execution_runtime: VoiceCallExecutionRuntime



    def start(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Prepare room and start execution.
        """


        room_configuration = (
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
            "room": room_configuration,
            "session": session,
        }